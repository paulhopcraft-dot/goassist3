# MetaHuman Setup Guide

This guide explains how to set up Unreal Engine with MetaHuman to receive live facial animation from GoAssist.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GoAssist Backend                         │
│  ┌─────────┐    ┌───────────┐    ┌─────────────────────┐   │
│  │  Audio  │───→│ Audio2Face│───→│ ARKit-52 Blendshapes│   │
│  │   TTS   │    │   / LAM   │    └──────────┬──────────┘   │
│  └─────────┘    └───────────┘               │              │
│                                              │              │
│                              ┌───────────────▼────────────┐ │
│                              │    LiveLinkSender (UDP)    │ │
│                              └───────────────┬────────────┘ │
└──────────────────────────────────────────────┼──────────────┘
                                               │
                                          UDP :11111
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      Unreal Engine 5                          │
│  ┌────────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │ Live Link Face │───→│ MetaHuman BP │───→│  MetaHuman  │  │
│  │    Plugin      │    │  (Animation) │    │   (Mesh)    │  │
│  └────────────────┘    └──────────────┘    └─────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Unreal Engine 5.3+** (5.4 recommended)
   - Download from [Epic Games Launcher](https://www.unrealengine.com/download)
   - Free for revenue < $1M/year

2. **MetaHuman Plugin** (included with UE5)
   - Enable in Plugins menu

3. **Live Link Face Plugin** (included with UE5)
   - Enable in Plugins menu

## Step 1: Create MetaHuman

### Option A: MetaHuman Creator (Recommended)
1. Go to [metahuman.unrealengine.com](https://metahuman.unrealengine.com)
2. Sign in with Epic Games account
3. Create your avatar (free)
4. Export to Unreal Engine via Quixel Bridge

### Option B: Use Sample MetaHuman
1. Open Epic Games Launcher
2. Go to Unreal Engine > Samples
3. Download "MetaHuman Sample"

## Step 2: Set Up Unreal Project

### Create New Project
```
1. Open Unreal Engine
2. Games > Blank
3. Name: "GoAssistAvatar"
4. Create Project
```

### Enable Required Plugins
```
Edit > Plugins > Search:

✓ Live Link
✓ Live Link Face
✓ MetaHuman
✓ Quixel Bridge (for importing MetaHumans)
```

Restart editor after enabling.

### Import MetaHuman
```
1. Window > Quixel Bridge
2. Sign in
3. Find your MetaHuman
4. Click "Add" to import
5. Wait for download (~2-5 GB per MetaHuman)
```

## Step 3: Configure Live Link

### Add Live Link Source
```
1. Window > Virtual Production > Live Link
2. Click "+ Source"
3. Select "LiveLinkFace Source"
4. Enter GoAssist IP (default: 127.0.0.1)
5. Port: 11111
```

### Verify Connection
When GoAssist is running, you should see:
- "GoAssist" subject appear in Live Link panel
- Green status indicator
- Frame data updating

## Step 4: Connect to MetaHuman

### Create Blueprint
1. Right-click in Content Browser
2. Blueprint Class > Actor
3. Name: "BP_GoAssistAvatar"

### Add MetaHuman Component
```cpp
// In Blueprint:
1. Add Component > Skeletal Mesh
2. Set Mesh to your MetaHuman face
3. Add Component > Live Link Face
```

### Configure Live Link Face Component
```
Live Link Face Component Settings:
- Subject Name: "GoAssist"
- Apply to Mesh: (your MetaHuman face mesh)
- Blend Shapes Only: ✓
```

### Blueprint Event Graph
```
Event BeginPlay
    └→ Get Live Link Face Component
        └→ Set Subject Name: "GoAssist"
        └→ Set Active: True
```

## Step 5: Test Integration

### Start GoAssist Backend
```bash
cd goassist3
python -m uvicorn src.main:app --host 0.0.0.0 --port 8081
```

### Run Test Script
```bash
python -c "
import asyncio
from src.animation.livelink import create_livelink_sender
from src.animation.base import get_neutral_blendshapes

async def test():
    sender = create_livelink_sender()
    await sender.start('GoAssist')

    # Send test frames
    blendshapes = get_neutral_blendshapes()
    for i in range(100):
        # Animate jaw for testing
        blendshapes['jawOpen'] = 0.5 * (1 + (i % 20) / 20)
        await sender.send_frame(blendshapes, i * 33)
        await asyncio.sleep(0.033)

    await sender.stop()

asyncio.run(test())
"
```

### Verify in Unreal
1. Press Play in editor
2. MetaHuman face should animate
3. Jaw should move up/down with test data

## Step 6: Production Setup

### Optimize for Performance
```
Project Settings > Engine > Rendering:
- Anti-Aliasing: TAA (not MSAA)
- Shadow Quality: Medium
- Global Illumination: Lumen (or Screen Space for lower-end)
```

### Configure for Streaming (Optional)
For web deployment via Pixel Streaming:
```
1. Enable Pixel Streaming plugin
2. Configure signaling server
3. Set up TURN/STUN for WebRTC
```

## Troubleshooting

### No Connection in Live Link
- Check firewall allows UDP 11111
- Verify GoAssist is sending (check logs)
- Ensure correct IP address

### MetaHuman Not Animating
- Verify Live Link Face component is active
- Check subject name matches ("GoAssist")
- Ensure ARKit-52 blendshape names match

### Low FPS / Stuttering
- Reduce MetaHuman LOD
- Disable hair simulation
- Lower shadow quality
- Check network latency

### Blendshapes Look Wrong
- Verify blendshape values are 0.0-1.0
- Check for correct ARKit-52 naming
- Test with neutral pose first

## API Reference

### Live Link Packet Format
```json
{
    "DeviceID": "GoAssist",
    "Timestamp": 123.456,
    "Blendshapes": {
        "browDownLeft": 0.0,
        "browDownRight": 0.0,
        "browInnerUp": 0.0,
        ...
    },
    "HeadRotation": {
        "Pitch": 0.0,
        "Yaw": 0.0,
        "Roll": 0.0
    }
}
```

### Supported Blendshapes
All 52 ARKit blendshapes are supported:
- Brows: browDownLeft, browDownRight, browInnerUp, browOuterUpLeft, browOuterUpRight
- Eyes: eyeBlinkLeft, eyeBlinkRight, eyeLookDownLeft, eyeLookDownRight, etc.
- Jaw: jawForward, jawLeft, jawOpen, jawRight
- Mouth: mouthClose, mouthDimpleLeft, mouthDimpleRight, etc.
- Nose: noseSneerLeft, noseSneerRight
- Cheeks: cheekPuff, cheekSquintLeft, cheekSquintRight
- Tongue: tongueOut

## Resources

- [MetaHuman Documentation](https://docs.metahuman.unrealengine.com/)
- [Live Link Documentation](https://docs.unrealengine.com/5.0/en-US/live-link-in-unreal-engine/)
- [ARKit Face Tracking](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)
