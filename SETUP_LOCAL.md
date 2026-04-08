# MyLittleAgent - Local Setup

This setup avoids depending on `uv` and uses a plain Python virtual environment plus npm.

## 1. Python environment

From the project root:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Windows CMD

```cmd
.venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### WSL / bash

```bash
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 2. Environment file

Create a local env file from the example:

```bash
copy .env.example .env
```

On bash/WSL:

```bash
cp .env.example .env
```

Then set at least:

- `API_KEY`
- `BASE_URL`

## 3. Frontend dependencies

```bash
cd frontend
npm install
```

## 4. Run backend

From the project root with the Python virtual environment active:

```bash
python server_main.py --port 6400 --reload
```

## 5. Run frontend

From `frontend/`:

```bash
npm run dev
```

If needed, set the backend base URL explicitly:

### PowerShell

```powershell
$env:VITE_API_BASE_URL='http://localhost:6400'
npm run dev
```

### CMD

```cmd
set VITE_API_BASE_URL=http://localhost:6400
npm run dev
```

### bash / WSL

```bash
VITE_API_BASE_URL=http://localhost:6400 npm run dev
```

## 6. Access

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:6400`

## 7. Current note

This project is in migration. Visible naming has already started moving to MyLittleAgent, while deeper runtime/docs references may still mention ChatDev or DevAll until further refactoring.
