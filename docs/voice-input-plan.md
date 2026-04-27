# Voice Input for User Preferences — Implementation Plan

## Overview
Enable users to speak their restaurant preferences naturally across all client surfaces (Streamlit, React frontend, CLI). Speech is transcribed via OpenAI Whisper, then parsed into structured `UserPreferences` using the existing Groq LLM pipeline.

---

## Architecture Impact

| Phase | Impact Level | What Changes |
|-------|-------------|--------------|
| Phase 0 (CLI) | Medium | New `milestone1 voice-prefs` command for microphone-based input. |
| Phase 2 (Preferences) | High | New `voice_parser.py` module: transcribed text -> structured `UserPreferences` via LLM prompt. |
| Phase 3 (Integration) | Low-Medium | Reuse `build_integration_output`; no structural changes, but may need voice-specific prompt tuning. |
| Phase 6 (Backend API) | High | New `POST /api/v1/speech-to-preferences` endpoint: accepts audio, calls Whisper, parses transcript, returns `PreferencesRequest`. |
| Phase 7 (Frontend) | High | New `VoiceInput.jsx` component using MediaRecorder API; wires into `PreferenceForm` for auto-fill. |
| Phase 8 (Streamlit) | High | New voice recorder widget (custom HTML/JS component) in `src/phase8/app.py`; calls backend STT endpoint. |

---

## Technical Approach

### 1. Speech-to-Text (STT)
- **Service:** OpenAI Whisper API (`openai.audio.transcriptions.create`)
- **Audio source:** Browser MediaRecorder (WebM/Opus) for web clients; `sounddevice` + WAV for CLI.
- **Format conversion:** `pydub` or `ffmpeg` to convert WebM -> WAV/MP3 before sending to Whisper.
- **Key constraint:** Whisper API accepts files up to 25 MB. Typical 10-15s voice clip is well under this.

### 2. Natural Language to Structured Preferences
- **Parser:** Groq LLM (already configured) with a dedicated structured-extraction prompt.
- **Prompt design:** System message defines the 5 fields (`location`, `budget_band`, `cuisines`, `minimum_rating`, `additional_preferences`) and asks the model to extract them from the user transcript.
- **Validation:** Reuse existing `preferences_from_mapping` in Phase 2 to validate LLM output against allowed cities/cuisines.
- **Fallback:** If LLM extraction fails, return raw transcript to user for manual editing.

### 3. Audio Recording by Client

| Client | Recording Method | Library / API |
|--------|-----------------|---------------|
| Streamlit | Custom HTML component injected via `st.components.v1.html` | Browser `MediaRecorder` API |
| React | Native hook | `MediaRecorder` API + `useState` for blob management |
| CLI | Python mic capture | `sounddevice` + `scipy.io.wavfile` |

---

## Detailed Code Changes

### Phase 6: New Backend Endpoint

**New file:** `src/phase6/api/routers/voice.py`

```python
@router.post("/speech-to-preferences")
async def speech_to_preferences(
    audio: UploadFile = File(...),
    allowed_cities: list[str] | None = Query(default=None),
) -> PreferencesRequest:
    # 1. Save uploaded audio to temp file
    # 2. Convert WebM/Opus -> MP3 via pydub (if needed)
    # 3. Call Whisper API: openai.audio.transcriptions.create(model="whisper-1", file=...)
    # 4. Call Groq LLM to extract structured preferences from transcript
    # 5. Validate via preferences_from_mapping
    # 6. Return PreferencesRequest
```

**Modified files:**
- `src/phase6/api/main.py` — include `voice` router.
- `src/phase6/api/schemas.py` — add `SpeechToTextResponse` if needed.
- `src/phase6/api/service.py` — add `_transcribe_audio()` and `_extract_preferences_from_transcript()` helpers.

**New dependency:** `openai` (add to `pyproject.toml`).

### Phase 2: Voice Parser Module

**New file:** `src/phase2/preferences/voice_parser.py`

```python
def parse_preferences_from_transcript(
    transcript: str,
    allowed_cities: set[str] | None = None,
    allowed_cuisines: list[str] | None = None,
) -> UserPreferences:
    """
    Use Groq LLM to extract structured preferences from free-form voice text.
    """
    # Build extraction prompt
    # Call call_groq_model (from phase4) or internal LLM client
    # Parse JSON response into UserPreferences
    # Validate with preferences_from_mapping as fallback
```

**Design decision:** This module can either:
- (A) Import `phase4.llm.client.call_groq_model` directly, or
- (B) Accept an injected LLM client to avoid cross-phase coupling.

**Recommendation:** Option (A) is acceptable for Milestone 1 since Phase 4 is already stable. Refactor to (B) if Phase 4 internals change frequently.

### Phase 8 (Streamlit): Voice Widget

**Modified file:** `src/phase8/app.py`

Add a new section above the form:

```python
# Voice input widget
st.subheader("Or speak your preferences")
audio_bytes = _record_audio_component()
if audio_bytes:
    with st.spinner("Transcribing..."):
        result = requests.post(
            "http://localhost:8000/api/v1/speech-to-preferences",
            files={"audio": ("recording.webm", audio_bytes, "audio/webm")},
        )
    if result.ok:
        voice_prefs = result.json()
        st.session_state["voice_prefs"] = voice_prefs
        st.success("Preferences captured from voice!")
    else:
        st.error("Could not understand. Please try again or type manually.")
```

**New helper:** `_record_audio_component()` uses `st.components.v1.html` to embed a small JavaScript snippet that uses `MediaRecorder` to capture audio and returns it as base64 to Python via `st.session_state` or `streamlit-js-eval`.

**Alternative:** Use `streamlit-audiorecorder` from PyPI (simpler but adds a dependency).

### Phase 7 (React): Voice Input Component

**New file:** `frontend/src/components/VoiceInput.jsx`

```jsx
export default function VoiceInput({ onPreferencesExtracted }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");

  const startRecording = async () => {
    // navigator.mediaDevices.getUserMedia({ audio: true })
    // new MediaRecorder(stream)
    // onstop -> send blob to /api/v1/speech-to-preferences
    // onPreferencesExtracted(response.data)
  };

  return (
    <button onClick={startRecording} className={isRecording ? "recording" : ""}>
      {isRecording ? "Listening..." : "Speak Preferences"}
    </button>
  );
}
```

**Modified file:** `frontend/src/components/PreferenceForm.jsx` — wire `VoiceInput` so extracted preferences auto-populate form fields.

### Phase 0 (CLI): Voice Command

**Modified file:** `src/phase0/cli.py`

Add subcommand:

```bash
milestone1 voice-prefs
```

Flow:
1. Check `sounddevice` is installed.
2. Record 10 seconds (or until silence detected) to a temp WAV file.
3. Send WAV to backend `/api/v1/speech-to-preferences` (or call Whisper directly if running offline).
4. Print extracted preferences as JSON or pretty table.
5. Ask user: "Submit these preferences? [Y/n]"

**New dependency:** `sounddevice`, `scipy` (for CLI only; add to optional deps).

---

## Data Flow

```
User speaks
    |
    v
[Client records audio]  -->  (WebM/Opus blob or WAV)
    |
    v
POST /api/v1/speech-to-preferences
    |
    +---> Convert audio format (pydub)
    +---> Whisper API --> Transcript text
    +---> Groq LLM extraction prompt --> Structured JSON
    +---> Phase 2 validation --> UserPreferences
    |
    v
Return PreferencesRequest DTO
    |
    v
Client auto-fills form fields
```

---

## Audio Format & Conversion Strategy

| Source Format | Target Format | Tool | Notes |
|---------------|---------------|------|-------|
| WebM/Opus (browser) | MP3 or WAV | `pydub` | Whisper accepts mp3, mp4, mpeg, mpga, m4a, wav, webm. WebM is actually accepted, but Opus codec inside WebM may cause issues. Converting to MP3 is safest. |
| WAV (CLI) | WAV | None | Already compatible. |

**Recommended dependency:** `pydub` + system `ffmpeg` (or `ffmpeg-python`). For deployment, include `ffmpeg` in Dockerfile or use a Python-only converter like `audioop` for simple WAV conversions.

---

## New Dependencies

| Package | Where | Purpose |
|---------|-------|---------|
| `openai` | Backend | Whisper API client |
| `pydub` | Backend | Audio format conversion |
| `streamlit-js-eval` or `streamlit-audiorecorder` | Phase 8 (optional) | Easier audio capture in Streamlit |
| `sounddevice` | Phase 0 (CLI) | Microphone recording |
| `scipy` | Phase 0 (CLI) | Save WAV files |

---

## Security & Privacy Considerations

1. **No audio persistence:** Delete temp audio files immediately after transcription. Do not log audio bytes.
2. **No PII in logs:** Log only that a voice request was made, plus duration and success/failure. Never log the transcript at INFO level.
3. **Rate limiting:** Apply stricter rate limits on `/speech-to-preferences` than text endpoints (e.g., 10 requests/minute per IP) because STT is more expensive.
4. **HTTPS only:** Browsers require HTTPS for `MediaRecorder` with `getUserMedia` in production. Document this for deployers.

---

## Error Handling & Empty States

| Scenario | UX Behavior |
|----------|-------------|
| Microphone permission denied | Show inline error: "Please allow microphone access in your browser settings." |
| Audio too quiet / empty | Show: "No speech detected. Please speak clearly and try again." |
| Whisper fails (network, rate limit) | Show: "Speech service temporarily unavailable. Please type your preferences instead." |
| LLM extraction fails / incomplete | Show raw transcript + editable form fields pre-filled with whatever was extracted. |
| Unknown location in transcript | Show validation error: "We heard 'XYZ' but couldn't match it to a known city. Please select from the list." |

---

## Implementation Order (Recommended)

1. **Backend foundation** (Phase 6)
   - Add `openai` and `pydub` dependencies.
   - Build `POST /api/v1/speech-to-preferences` endpoint.
   - Write unit tests with sample audio fixtures (generate synthetic WAVs for CI).

2. **Voice parser** (Phase 2)
   - Implement `voice_parser.py` with LLM extraction prompt.
   - Test with sample transcripts: "I want Italian food in Bangalore under medium budget with at least 4 stars."

3. **Streamlit integration** (Phase 8)
   - Add audio recorder widget.
   - Wire to backend endpoint.
   - Add auto-fill logic for form fields.

4. **React frontend** (Phase 7)
   - Build `VoiceInput.jsx` with MediaRecorder.
   - Integrate into `PreferenceForm.jsx`.

5. **CLI** (Phase 0)
   - Add `milestone1 voice-prefs` command.
   - Optional: offline mode that calls Whisper directly without backend.

6. **Documentation update**
   - Update `README.md` with voice feature instructions.
   - Update `docs/streamlit-deploy.md` with mic permission notes for HTTPS.

---

## Performance Notes

- **Latency budget:**
  - Audio upload: 1-2s (depending on connection)
  - Whisper transcription: 1-3s
  - Groq LLM extraction: 1-2s
  - **Total: ~3-7s** end-to-end for a typical 5-second utterance.
- **Optimization:** Stream audio directly to backend while recording (chunked upload) to reduce perceived latency. This is advanced and can be deferred to a later iteration.
- **Cost:** Whisper API is $0.006/minute. A 10-second clip costs ~$0.001. Negligible for demo scale; monitor if scaling.
