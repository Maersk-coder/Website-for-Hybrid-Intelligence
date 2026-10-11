// SETTINGS: every number and colour for the animation section, in one place.
const SETTINGS = {
  // The dot cloud 
  points: window.innerWidth < 800 ? 3500 : 7000, // how many dots (fewer on phones)
  dotSize: 2.1,             // size of each dot
  dotColor: 0x1b1660,       // main dot colour (deep navy)
  accentColor: 0x4a63e0,    // a few brighter blue dots
  spinSpeed: 0.12,          // how fast the cloud turns
  phoneOpacity: 0.35,       // on phones the cloud sits faintly behind the text

  // Shape changes 
  holdSeconds: 4.5,         // how long each shape stays
  morphSeconds: 2.4,        // how long the change between shapes takes
  phases: [                 // the shapes in order, and the word shown with each
    { shape: "human", word: "Human creativity." },
    { shape: "machine", word: "Machine precision." },
    { shape: "hybrid", word: "Mutual learning." },
  ],

  // Mouse 
  tiltAmount: 0.4,          // how much the mouse tilts the cloud
  tiltSmoothness: 0.04,     // lower = the tilt follows the mouse more slowly

  // Lines 
  lineColor: "63, 81, 181", // contour and pointer lines (indigo, as red, green, blue)
  contourRings: 22,         // how many flowing loops around the cloud
  contourDrift: 0.09,       // how far each bigger loop moves to the left

  // Labels 
  // where each label sits, measured from the cloud's centre in "cloud sizes" [right, down]
  labelSpots: [
    [-0.35, -1.45], // 01 above
    [1.2, -0.8],    // 02 top right
    [1.15, 0.85],   // 03 bottom right
    [-1.35, 1.3],   // 04 bottom left (clear of the card)
  ],
  // the point on the cloud each label points at [x, y, z]; these turn with the cloud
  labelTargets: [
    [0.15, 0.95, 0.25],
    [0.9, 0.4, 0.3],
    [0.8, -0.55, 0.35],
    [-0.3, -0.9, 0.3],
  ],
};
