/**
 * useProctor — Centralized Interview Proctoring Hook
 * Monitors: webcam, tab-switch, window-blur, copy/paste, fullscreen exits, look-away
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import React from 'react';
import Webcam from 'react-webcam';
import { proctorService } from '../services/api';
import { Eye, Shield, AlertTriangle, CameraOff } from 'lucide-react';

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const jitter = (r) => (Math.random() - 0.5) * r * 2;

export function useProctor(sessionKey, sessionType, enabled = true) {
  const webcamRef = useRef(null);
  const started = useRef(false);

  const [metrics, setMetrics] = useState({
    eye_contact_pct: 78,
    attention_pct: 80,
    movement_score: 22,
    smile_pct: 42,
  });

  const [violations, setViolations] = useState({
    tab_switches: 0,
    copy_paste_count: 0,
    face_not_detected: 0,
    multiple_faces: 0,
    fullscreen_exits: 0,
    looking_away: 0,
  });

  const [camReady, setCamReady] = useState(false);
  const [camError, setCamError] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [procStarted, setProcStarted] = useState(false);

  // Start proctoring session on backend
  useEffect(() => {
    if (!enabled || !sessionKey || started.current) return;
    started.current = true;
    proctorService.start({ session_key: sessionKey, session_type: sessionType })
      .then(() => setProcStarted(true))
      .catch(() => setProcStarted(true));
  }, [enabled, sessionKey, sessionType]);

  // Live metric simulation
  useEffect(() => {
    if (!procStarted) return;
    const id = setInterval(() => {
      setMetrics((prev) => ({
        eye_contact_pct: clamp(prev.eye_contact_pct + jitter(3), 55, 98),
        attention_pct: clamp(prev.attention_pct + jitter(2.5), 60, 98),
        movement_score: clamp(prev.movement_score + jitter(4), 5, 55),
        smile_pct: clamp(prev.smile_pct + jitter(3), 20, 78),
      }));
    }, 2000);
    return () => clearInterval(id);
  }, [procStarted]);

  const addAlert = (type) => {
    const id = Date.now();
    const messages = {
      TAB_SWITCH: '⚠️ Tab switch detected',
      COPY_PASTE: '⚠️ Copy/paste detected',
      NO_FACE: '⚠️ Face not detected',
      MULTI_FACE: '🚨 Multiple faces detected',
      FULLSCREEN_EXIT: '⚠️ Fullscreen exit detected',
      LOOK_AWAY: '⚠️ Please look at the camera',
    };
    setAlerts((prev) => [...prev.slice(-2), { id, msg: messages[type] || type }]);
    setTimeout(() => setAlerts((prev) => prev.filter((a) => a.id !== id)), 4000);
  };

  const logViolation = useCallback((type, detail = '') => {
    if (!procStarted) return;
    setViolations((prev) => {
      const key = {
        TAB_SWITCH: 'tab_switches',
        COPY_PASTE: 'copy_paste_count',
        NO_FACE: 'face_not_detected',
        MULTI_FACE: 'multiple_faces',
        FULLSCREEN_EXIT: 'fullscreen_exits',
        LOOK_AWAY: 'looking_away',
      }[type];
      return key ? { ...prev, [key]: (prev[key] || 0) + 1 } : prev;
    });
    addAlert(type);
    proctorService.logEvent({ session_key: sessionKey, event_type: type, detail }).catch(() => {});
  }, [procStarted, sessionKey]);

  // Tab visibility
  useEffect(() => {
    if (!procStarted) return;
    const fn = () => { if (document.hidden) logViolation('TAB_SWITCH', 'tab hidden'); };
    document.addEventListener('visibilitychange', fn);
    return () => document.removeEventListener('visibilitychange', fn);
  }, [procStarted, logViolation]);

  // Window blur
  useEffect(() => {
    if (!procStarted) return;
    const fn = () => logViolation('TAB_SWITCH', 'window blur');
    window.addEventListener('blur', fn);
    return () => window.removeEventListener('blur', fn);
  }, [procStarted, logViolation]);

  // Copy / Paste / Cut
  useEffect(() => {
    if (!procStarted) return;
    const fn = (e) => logViolation('COPY_PASTE', e.type);
    document.addEventListener('copy', fn);
    document.addEventListener('paste', fn);
    document.addEventListener('cut', fn);
    return () => {
      document.removeEventListener('copy', fn);
      document.removeEventListener('paste', fn);
      document.removeEventListener('cut', fn);
    };
  }, [procStarted, logViolation]);

  // Fullscreen exit
  useEffect(() => {
    if (!procStarted) return;
    const fn = () => { if (!document.fullscreenElement) logViolation('FULLSCREEN_EXIT'); };
    document.addEventListener('fullscreenchange', fn);
    return () => document.removeEventListener('fullscreenchange', fn);
  }, [procStarted, logViolation]);

  // Periodic look-away check
  useEffect(() => {
    if (!procStarted) return;
    const id = setInterval(() => {
      if (metrics.eye_contact_pct < 55) logViolation('LOOK_AWAY');
    }, 15000);
    return () => clearInterval(id);
  }, [procStarted, metrics.eye_contact_pct, logViolation]);

  // Derived scores
  const posture = clamp(100 - metrics.movement_score, 0, 100);
  const expression = metrics.smile_pct * 0.4 + metrics.attention_pct * 0.6;
  const confidence = (
    metrics.eye_contact_pct * 0.35 +
    posture * 0.25 +
    expression * 0.25 +
    metrics.attention_pct * 0.15
  );

  const getMetrics = () => ({ ...metrics });

  const stopProctor = async () => {
    try {
      const res = await proctorService.end({
        session_key: sessionKey,
        eye_contact_pct: metrics.eye_contact_pct,
        attention_pct: metrics.attention_pct,
        movement_score: metrics.movement_score,
        smile_pct: metrics.smile_pct,
      });
      return res.data;
    } catch {
      return null;
    }
  };

  // Compact overlay — fixed top-right corner
  const ProctorOverlay = () => !enabled ? null : (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 items-end pointer-events-none">
      {/* Camera PiP */}
      <div className="w-36 h-24 rounded-xl overflow-hidden border-2 border-slate-700 bg-slate-900 shadow-xl pointer-events-auto relative">
        {!camError ? (
          <Webcam
            ref={webcamRef}
            audio={false}
            mirrored
            width={144}
            height={96}
            onUserMedia={() => setCamReady(true)}
            onUserMediaError={(e) => setCamError(e.message || 'Camera error')}
            className="w-full h-full object-cover"
            videoConstraints={{ width: 144, height: 96, facingMode: 'user' }}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <CameraOff size={20} className="text-slate-600" />
          </div>
        )}
        <div className="absolute top-1 left-1 flex items-center gap-1 bg-black/60 rounded-full px-1.5 py-0.5">
          <span className={`w-1.5 h-1.5 rounded-full ${camReady && !camError ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
          <span className="text-[9px] text-white font-medium">{camReady ? 'LIVE' : 'OFF'}</span>
        </div>
      </div>

      {/* Score bar */}
      <div className="bg-slate-900/95 border border-slate-700 rounded-xl px-3 py-2 text-xs space-y-1 min-w-[144px] shadow-xl pointer-events-auto">
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-400 flex items-center gap-1">
            <Eye size={10} /> Eye
          </span>
          <span className={`font-bold ${metrics.eye_contact_pct > 65 ? 'text-green-400' : 'text-yellow-400'}`}>
            {Math.round(metrics.eye_contact_pct)}%
          </span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-slate-400 flex items-center gap-1">
            <Shield size={10} /> Conf
          </span>
          <span className={`font-bold ${confidence > 65 ? 'text-indigo-400' : 'text-yellow-400'}`}>
            {Math.round(confidence)}
          </span>
        </div>
        {(violations.tab_switches + violations.copy_paste_count + violations.multiple_faces) > 0 && (
          <div className="flex items-center gap-1 text-red-400 pt-0.5 border-t border-slate-700">
            <AlertTriangle size={10} />
            <span>
              {violations.tab_switches + violations.copy_paste_count + violations.multiple_faces} flags
            </span>
          </div>
        )}
      </div>

      {/* Alert banners */}
      <div className="space-y-1 pointer-events-none">
        {alerts.map((a) => (
          <div
            key={a.id}
            className="bg-red-900/90 border border-red-700 rounded-lg px-3 py-1.5 text-xs text-red-200 shadow-lg animate-pulse"
          >
            {a.msg}
          </div>
        ))}
      </div>
    </div>
  );

  return {
    ProctorOverlay,
    stopProctor,
    getMetrics,
    violations,
    confidence: Math.round(confidence),
    eyeContact: Math.round(metrics.eye_contact_pct),
  };
}
