#version 120

/*
 * Reny Shaders — Deferred Pass Vertex Shader
 * Executed between terrain and translucent/water rendering
 */

varying vec2 texcoord;

void main() {
    gl_Position = ftransform();
    texcoord = gl_MultiTexCoord0.xy;
}
