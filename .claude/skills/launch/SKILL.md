---
name: launch
description: Launch the application in a browser - detects project type, starts server, opens browser automatically
version: 1.0.0
---

# Launch Skill - Start Application in Browser

You are now in **Launch Mode** - automatically start the application's dev server and open it in a browser.

## Mission

Launch the application with zero manual steps:
1. **Detect** project type and available launch scripts
2. **Start** appropriate dev server in background
3. **Wait** for server to be ready (port listening)
4. **Open** browser at the correct URL
5. **Report** status and URL to user

**Key Principle**: One command to go from code to running application.

---

## Process

### Step 1: Detect Launch Configuration

**Check package.json** for launch scripts:

```bash
# Read package.json
cat package.json | grep -A 5 '"scripts"'
```

**Common Script Patterns**:
- `dashboard:web` → Web dashboard (govertical)
- `dev` → Development server (Next.js, Vite, etc.)
- `start` → Production/dev server
- `serve` → Static file server
- `preview` → Preview build

**Port Detection**:
- Check script for explicit port (e.g., `-p 3000`)
- Check for environment variables (PORT=)
- Fall back to common defaults (3000, 8080, 5173, etc.)

### Step 2: Start Server

**Run in background**:
```bash
# Start server in background with output capture
npm run [script-name] > /tmp/server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"
```

**Alternative for Windows**:
```bash
# PowerShell background job
powershell -Command "Start-Process npm -ArgumentList 'run','dashboard:web' -WindowStyle Hidden"
```

### Step 3: Wait for Server Ready

**Poll port until listening**:
```bash
# Function to check if port is listening
check_port() {
    local port=$1
    nc -z localhost $port 2>/dev/null || \
    powershell -Command "Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet" 2>/dev/null
}

# Wait up to 30 seconds
PORT=3000
MAX_WAIT=30
WAITED=0

echo "Waiting for server on port $PORT..."
while ! check_port $PORT && [ $WAITED -lt $MAX_WAIT ]; do
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "❌ Server failed to start within 30 seconds"
    exit 1
fi

echo "✓ Server ready on port $PORT"
```

### Step 4: Open Browser

**Cross-platform browser launch**:
```bash
URL="http://localhost:3000"

# Detect OS and open browser
if command -v xdg-open > /dev/null; then
    # Linux
    xdg-open "$URL"
elif command -v open > /dev/null; then
    # macOS
    open "$URL"
elif command -v start > /dev/null; then
    # Windows
    start "$URL"
else
    # Fallback: PowerShell
    powershell -Command "Start-Process '$URL'"
fi

echo "✓ Opened browser at $URL"
```

### Step 5: Report Status

**Final output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Application Launched
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: govertical
Server: npm run dashboard:web
URL: http://localhost:3000
PID: 12345

Status: ✓ Running

To stop server:
  kill 12345
  OR: npm run stop (if available)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Project-Specific Configurations

### govertical (Dashboard)

**Detect**:
```json
{
  "scripts": {
    "dashboard:web": "node dist/web/server.js"
  }
}
```

**Launch**:
- Script: `npm run dashboard:web`
- Port: 3000 (default Express port)
- URL: `http://localhost:3000`
- Type: Revenue dashboard with metrics

### goassist3 (Avatar Application)

**Detect**:
```json
{
  "scripts": {
    "dev": "vite",
    "start": "node server/index.js"
  }
}
```

**Launch**:
- Script: `npm run dev` OR `npm start`
- Port: 5173 (Vite default) or from config
- URL: `http://localhost:5173`
- Type: Voice/avatar application

### gpnet3 (Healthcare Application)

**Detect**:
```json
{
  "scripts": {
    "dev": "next dev",
    "start": "next start"
  }
}
```

**Launch**:
- Script: `npm run dev`
- Port: 3000 (Next.js default)
- URL: `http://localhost:3000`
- Type: Healthcare web application

---

## Smart Detection Logic

### Priority Order

1. **Explicit dashboard script** (`dashboard:web`, `dashboard`)
   - Most specific, user clearly wants this

2. **Development server** (`dev`)
   - Standard for modern frameworks

3. **Start script** (`start`)
   - Could be prod or dev, check if already built

4. **Preview/serve** (`preview`, `serve`)
   - For static builds

5. **Custom detection**
   - Look for framework-specific files (vite.config, next.config)
   - Infer appropriate command

### Port Detection Strategy

**1. From package.json script**:
```json
"dev": "vite --port 5173"
```
→ Extract port: 5173

**2. From config files**:
- `vite.config.ts` → server.port
- `next.config.js` → custom port
- `.env` → PORT variable

**3. Framework defaults**:
- Vite: 5173
- Next.js: 3000
- Express: 3000
- Create React App: 3000
- Angular: 4200
- Vue CLI: 8080

**4. Active port scanning**:
```bash
# Find what port the process actually opened
lsof -i -P -n | grep LISTEN | grep node
```

---

## Error Handling

### Server Fails to Start

```bash
if ! check_server_started; then
    echo "❌ Server failed to start"
    echo "Checking logs..."
    tail -20 /tmp/server.log

    # Common issues:
    echo "Common problems:"
    echo "  - Port already in use (check: lsof -i :3000)"
    echo "  - Build missing (run: npm run build)"
    echo "  - Dependencies missing (run: npm install)"

    exit 1
fi
```

### Port Already in Use

```bash
check_port_in_use() {
    local port=$1
    if check_port $port; then
        echo "⚠️  Port $port already in use"
        echo "Options:"
        echo "  1. Kill existing process: lsof -ti:$port | xargs kill"
        echo "  2. Use different port: PORT=3001 npm run dev"
        echo "  3. Launch anyway (will fail)"
        read -p "Continue? (y/N): " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
}
```

### Build Required

```bash
if [ -f "dist/index.html" ] || [ -f "build/index.html" ]; then
    echo "✓ Build exists"
else
    echo "⚠️  No build found"
    read -p "Run build first? (Y/n): " choice
    if [[ ! "$choice" =~ ^[Nn]$ ]]; then
        npm run build
    fi
fi
```

---

## Platform-Specific Commands

### Windows (PowerShell)

```powershell
# Start server in background
$job = Start-Job -ScriptBlock { npm run dashboard:web }
$jobId = $job.Id

# Wait for port
$port = 3000
$maxWait = 30
$waited = 0

Write-Host "Waiting for server on port $port..."
while ($waited -lt $maxWait) {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($connection) { break }
    Start-Sleep -Seconds 1
    $waited++
    Write-Host -NoNewline "."
}

if ($waited -ge $maxWait) {
    Write-Host "`n❌ Server failed to start"
    Stop-Job -Id $jobId
    exit 1
}

Write-Host "`n✓ Server ready"

# Open browser
Start-Process "http://localhost:$port"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "🚀 Application Launched"
Write-Host "URL: http://localhost:$port"
Write-Host "Job ID: $jobId"
Write-Host ""
Write-Host "To stop: Stop-Job -Id $jobId"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### macOS/Linux (Bash)

```bash
#!/bin/bash

# Start server
npm run dashboard:web &
SERVER_PID=$!

# Wait for port
PORT=3000
for i in {1..30}; do
    if nc -z localhost $PORT 2>/dev/null; then
        echo "✓ Server ready"
        break
    fi
    sleep 1
done

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:$PORT"
else
    xdg-open "http://localhost:$PORT"
fi

echo "🚀 Launched at http://localhost:$PORT (PID: $SERVER_PID)"
```

---

## Advanced Features

### Auto-Reload on Code Changes

If using Vite/Next.js, they handle this automatically.

For custom servers:
```bash
# Use nodemon for auto-reload
npm install --save-dev nodemon

# Update package.json
{
  "scripts": {
    "dev": "nodemon dist/web/server.js"
  }
}
```

### Launch with Environment

```bash
# Set environment before launch
ENV=development npm run dev

# Or with .env file
if [ -f .env.local ]; then
    export $(cat .env.local | xargs)
fi
npm run dev
```

### Launch Multiple Services

For projects with separate frontend/backend:
```bash
# Start backend
npm run server &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both
wait_for_port 3000  # Backend
wait_for_port 5173  # Frontend

# Open frontend (which proxies to backend)
open http://localhost:5173
```

---

## Example: Launch govertical Dashboard

### Execution Flow

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Detecting Launch Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: govertical
Found script: "dashboard:web": "node dist/web/server.js"
Detected port: 3000 (Express default)
Type: Revenue Control Tower Dashboard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Starting Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ npm run dashboard:web

> govertical@1.0.0 dashboard:web
> node dist/web/server.js

Waiting for server on port 3000..........✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Server Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Opening browser: http://localhost:3000
Status: Running (PID: 45678)

Dashboard Features:
  • Revenue metrics & growth tracking
  • Velocity vs targets
  • Active alerts by severity
  • Vertical leaderboard

To stop server:
  kill 45678
  OR: Ctrl+C in this terminal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Example: Launch goassist3 Avatar App

### Execution Flow

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Detecting Launch Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: goassist3
Found script: "dev": "vite"
Detected port: 5173 (Vite default)
Type: Voice/Avatar Application

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Starting Development Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ npm run dev

  VITE v4.5.0  ready in 432 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help

Waiting for server on port 5173..✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Avatar Application Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Opening browser: http://localhost:5173
Status: Running with hot-reload

Application Features:
  • Real-time voice conversation
  • Avatar rendering (blendshapes)
  • TTFA ≤ 250ms p95
  • Barge-in support

Press Ctrl+C to stop

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Integration with Toolkit

### After Feature Complete

When a feature is marked complete, suggest launch:

```
✓ Feature complete: Control Tower Dashboard

Would you like to launch the application? (Y/n)

→ User types 'y' or just presses Enter
→ Automatically runs /launch
→ Opens dashboard in browser
```

### Verify in Browser

Add to verification step:
```
PHASE 4: Verify
- ✓ Tests pass (npm test)
- ✓ Build successful (npm run build)
- → Launch in browser (/launch)
- → Manual verification: Does it work as expected?
```

---

## Future Enhancements

### v2: Smart Port Selection

If port in use, automatically find next available:
```bash
find_free_port() {
    local port=3000
    while lsof -i :$port > /dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}
```

### v3: Launch with Test Data

```bash
# Load fixtures before launch
npm run db:seed
npm run dev
```

### v4: Launch Profiles

```bash
/launch --profile production   # Production build
/launch --profile debug        # With debugger attached
/launch --profile performance  # With performance profiling
```

---

## Stop Server Command

Complementary `/stop` command:

```bash
# Find server PID
PID=$(lsof -ti:3000)

if [ -z "$PID" ]; then
    echo "No server running on port 3000"
else
    kill $PID
    echo "✓ Stopped server (PID: $PID)"
fi
```

---

**GO! Launch the application and open it in the browser.**
