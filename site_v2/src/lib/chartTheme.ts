// The charts' layout numbers: each drawing's size and margins in drawing units, and a text's offset
// from the point it labels in em of its own size. Every look value (colour, line, dot and text
// size) is in system.css.

export const scatter = {
  forms: [
    { cls: "chart-wide", width: 560, height: 330, left: 46 },
    { cls: "chart-narrow", width: 280, height: 230, left: 44 },
  ],
  right: 14,
  top: 12,
  bottom: 58,
  tick: 4,
  yTitleX: 11,
  // A label character's width, generous so a label moves before it meets the axis.
  labelChar: 7.7,
};

export const offset = {
  belowAxis: "1.2em",
  axisTitle: "2.5em",
  axisSubtitle: "3.9em",
  beside: "0.6em",
  middle: "0.35em",
  under: "1.85em",
};

// A strip plot keeps this share of its width free at each end, in percent, so no dot is cut.
export const stripInset = 3;
