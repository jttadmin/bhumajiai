# Universal AI Interview Assistant V4 (Windows 11)

A desktop interview **practice** application built with PySide6 and OpenAI. Use audio recording and AI assistance only with the participants’ permission and according to applicable interview rules. No screen-capture bypass or stealth features are included.

## New in V4
- Select a preset interview role or choose **Custom role...** and enter any job title.
- Paste a job description to tailor answers and feedback.
- Four answer styles: **Concise, Detailed, Scenario, STAR**.
- Load a PDF, DOCX, TXT or Markdown resume for answer personalization. Resume text is held in application memory and sent to OpenAI when generating answers/evaluations; it is not stored in the local history database.
- Preserves V3 continuous microphone transcription (8-second chunks), heuristic question detection, optional automatic answers, mock interview scoring, local SQLite history, floating window, shortcuts, and Windows EXE build script.

## Install
1. Install Python 3.12 x64 on Windows 11 and enable PATH.
2. Extract this ZIP and run `install_windows.bat`.
3. Run `start_windows.bat`.
4. Obtain an API key at https://platform.openai.com/api-keys and save it using the app's API key field (Windows Credential Manager via keyring).
5. Select a role, optionally paste a job description and load a resume, then enter or record questions.

## Packaging
Run `build_exe.bat` after installation. Expected output: `dist\UniversalInterviewAssistant.exe`. Windows builds must be run on Windows. This is an **unverified build target**, not a prebuilt EXE.

## Shortcuts
- `Ctrl+Enter`: ask AI
- `Ctrl+R`: start/stop single recording
- `Ctrl+Shift+I`: optional system-wide show/hide shortcut, if Windows permits it

## Audio, privacy, and cost
- Microphone-only capture (not system/meeting audio). Continuous mode sends approximately 8-second chunks to OpenAI transcription, so it is not low-latency streaming.
- Question detection uses a simple question-word / punctuation heuristic, not a dedicated AI classifier.
- Transcribed questions, generated answers, and evaluations may be stored locally in SQLite under `%LOCALAPPDATA%\BhumajiAI\DevOpsInterviewAssistant\history.db` (the V3 history location).
- The selected resume and job description may be sent to OpenAI with requests. Avoid uploading sensitive data without authorization.
- OpenAI API usage incurs separate charges.
- The model defaults to `gpt-4.1-mini`; change it in the UI if needed.

## Troubleshooting
- Check Windows Settings > Privacy & security > Microphone and allow desktop apps.
- Ensure your OpenAI API key has billing enabled and the chosen model is available.
- If global hotkeys are unavailable, use the tray menu. Some environments block keyboard hooks.
- For packaging failures, run the app from `start_windows.bat` first and inspect terminal errors.

## Testing status
Source has been syntax-checked in the build environment. Full Windows UI, audio, network API calls and EXE packaging require testing on a Windows 11 machine.

## Publish to GitHub

Create an empty GitHub repository named `universal-ai-interview-assistant` (do not initialize it with a README). From this extracted folder, run:

```powershell
git init
git add .
git commit -m "Initial commit: Universal AI Interview Assistant V4"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/universal-ai-interview-assistant.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. GitHub authentication may open a browser or require a credential manager. Never put API keys in commits, issues, or screenshots. Review `git status` before pushing.

The GitHub Actions workflow checks Python syntax on pushes and pull requests; it does not verify microphone capture, API connectivity, or Windows GUI behavior. Build the EXE on Windows with `build_exe.bat`.

## Security and privacy

Use this app only where recording and AI assistance are permitted. Avoid committing resumes, transcripts, interview history, or credentials. Resume/job-description context and transcribed questions may be transmitted to the configured API.
