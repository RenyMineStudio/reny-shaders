#version 120

/*
 * Reny Shaders — Deferred Pass Fragment Shader
 * Tests deferred stage capability, buffer writing, and pass sequencing
 */

/* DRAWBUFFERS:04 */

#include "/lib/common.glsl"

uniform sampler2D colortex0;

varying vec2 texcoord;

void main() {
    vec4 sceneColor = texture2D(colortex0, texcoord);

    // Output 0: preserve illuminated scene color for downstream passes
    gl_FragData[0] = sceneColor;

    // Output 1 (colortex4): write deferred stage marker signature to prove execution
    gl_FragData[1] = RENY_DEFERRED_MAGIC;
}
