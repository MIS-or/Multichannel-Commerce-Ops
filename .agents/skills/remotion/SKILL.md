---
name: remotion
description: |
    Programmatic video creation in React using Remotion.
    Guides building dynamic videos, animations, motion graphics, captions, data-driven
    visualizations, and rendering MP4/WebM video compositions with code.

    Relevant when:
      - Creating programmatic videos, social media clips, or product teasers.
      - Building motion graphics, kinetic typography, or animated charts in React.
      - Rendering videos with Remotion CLI or Lambda.
---

# Remotion: Programmatic Video Creation in React

Remotion allows developers to write real React components, CSS, and SVG, and render them as frame-accurate MP4 or WebM videos.

---

## 1. Core Remotion Concepts

- **`<Composition />`**: Defines a video entrypoint with `id`, `component`, `durationInFrames`, `fps`, `width`, and `height`.
- **`<Sequence />`**: Shifts timeline elements to start at a specific `from` frame for a specified `durationInFrames`.
- **`useCurrentFrame()`**: Returns the current integer frame number (0, 1, 2, ...).
- **`useVideoConfig()`**: Returns video metadata (`fps`, `durationInFrames`, `width`, `height`).
- **`interpolate()`**: Maps a frame number to a property value with clamping.
- **`spring()`**: Generates physics-based spring animations based on mass, damping, and stiffness.

---

## 2. Boilerplate Composition Example

```tsx
import {
    AbsoluteFill,
    interpolate,
    spring,
    useCurrentFrame,
    useVideoConfig,
} from 'remotion';

export const IntroTitle = ({ title }: { title: string }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Smooth entrance spring
    const scale = spring({
        frame,
        fps,
        config: { mass: 0.5, damping: 10, stiffness: 100 },
    });

    // Fade in opacity
    const opacity = interpolate(frame, [0, 20], [0, 1], {
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill
            style={{
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#090A0F',
            }}
        >
            <h1
                style={{
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                    fontSize: 80,
                    color: '#FFFFFF',
                    transform: `scale(${scale})`,
                    opacity,
                }}
            >
                {title}
            </h1>
        </AbsoluteFill>
    );
};
```

---

## 3. Video Rendering Commands

- Preview in browser: `npx remotion preview`
- Render to MP4: `npx remotion render src/index.ts MyComposition out/video.mp4`
