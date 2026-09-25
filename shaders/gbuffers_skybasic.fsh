#version 120

/* DRAWBUFFERS:0 */

varying vec4 color;

void main() {
    gl_FragData[0] = color;
}
