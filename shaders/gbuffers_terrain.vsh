#version 120

/*
 * Reny Shaders — Terrain GBuffer Vertex Shader
 * Probes mc_Entity, mc_midTexCoord, and at_tangent legacy attributes
 */

attribute vec4 mc_Entity;
attribute vec4 mc_midTexCoord;
attribute vec4 at_tangent;

varying vec4 color;
varying vec2 texcoord;
varying vec2 lmcoord;
varying vec3 normal;
varying float materialId;

void main() {
    gl_Position = ftransform();
    color = gl_Color;
    texcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    lmcoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    normal = normalize(gl_NormalMatrix * gl_Normal);
    
    // Pass block ID mapped by block.properties or raw ID
    materialId = mc_Entity.x;
}
