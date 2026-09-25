#version 120

/*
 * Reny Shaders — Composite Pass Fragment Shader
 * Tests capabilities:
 *  - colortex formats (RGBA8, RGBA32F, RGBA16F, R11F_G11F_B10F)
 *  - colortex skip-clear persistence (colortex3Clear = false)
 *  - uniforms: frameCounter, frameTime, frameTimeCounter, worldTime, sunPosition, camera
 *  - deferred pass data transfer verification (colortex4)
 *  - scale.composite directive testing
 */

/* DRAWBUFFERS:034 */

#include "/lib/common.glsl"
#include "/lib/probe_hud.glsl"

/*
Texture formats declaration (OptiFine E7 format contract)
Parsed by OptiFine ShaderPackParser from comments:
const int colortex0Format = RGBA8;
const int colortex1Format = RGBA32F;
const int colortex2Format = RGBA16F;
const int colortex3Format = RGBA8;
const int colortex4Format = R11F_G11F_B10F;

Skip framebuffer clear on colortex3 to enable persistence / history testing
const bool colortex3Clear = false;
*/

// Scale test: Check if OptiFine E7 acknowledges composite scaling
// (Historical research indicates this is an Iris/modern feature not present in E7)
/* scale.composite = 0.5 */

// Textures
uniform sampler2D colortex0; // Scene color from gbuffers & deferred
uniform sampler2D colortex1; // Gdepth / normals
uniform sampler2D colortex2; // Gnormal / encoded material ID
uniform sampler2D colortex3; // Persistent history buffer
uniform sampler2D colortex4; // Deferred signature buffer / R11F
uniform sampler2D depthtex0; // Depth buffer

// Core uniforms
uniform int frameCounter;
uniform float frameTime;
uniform float frameTimeCounter;
uniform int worldTime;
uniform vec3 sunPosition;
uniform vec3 cameraPosition;
uniform vec3 previousCameraPosition;
uniform mat4 gbufferModelView;
uniform mat4 gbufferPreviousModelView;
uniform mat4 gbufferProjection;
uniform mat4 gbufferPreviousProjection;
uniform float viewWidth;
uniform float viewHeight;

varying vec2 texcoord;

void main() {
    vec4 sceneColor = texture2D(colortex0, texcoord);

    // -------------------------------------------------------------------------
    // EXP-P0-HISTORY: Skip-clear persistence logic
    // -------------------------------------------------------------------------
    vec4 prevHistory = texture2D(colortex3, texcoord);
    vec4 updatedHistory = vec4(0.0);

    // Compute moving test marker location
    vec2 markerPos = getHistoryProbePos(frameCounter, frameTimeCounter);
    float distToMarker = distance(texcoord, markerPos);

    if (distToMarker < 0.025) {
        // Active marker head: solid bright color
        updatedHistory = vec4(1.0, 0.55, 0.1, 1.0);
    } else {
        // Trail decay: slowly fades previous pixel value
        // If colortex3Clear is functioning (i.e. clearing is skipped),
        // a smooth fading trail of ~25-30 frames remains visible.
        // If buffer is cleared every frame, previous value is always 0.
        updatedHistory = prevHistory * 0.96;
    }

    // -------------------------------------------------------------------------
    // EXP-P0-CAP: Deferred pass communication verification
    // -------------------------------------------------------------------------
    vec4 deferredSig = texture2D(colortex4, texcoord);
    // If deferred pass ran successfully, deferredSig matches RENY_DEFERRED_MAGIC
    bool deferredExecuted = distance(deferredSig.rgb, RENY_DEFERRED_MAGIC.rgb) < 0.05;

    // Preserve deferred verification status in alpha of colortex4
    vec4 outputColortex4 = deferredExecuted ? vec4(deferredSig.rgb, 1.0) : vec4(0.0, 0.0, 0.0, 0.0);

    // Outputs:
    // gl_FragData[0] -> colortex0 (scene color)
    // gl_FragData[1] -> colortex3 (history persistence buffer)
    // gl_FragData[2] -> colortex4 (deferred status / R11F_G11F_B10F test)
    gl_FragData[0] = sceneColor;
    gl_FragData[1] = updatedHistory;
    gl_FragData[2] = outputColortex4;
}
