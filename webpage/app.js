// ============================================================================
// Main Application - Canvas Drawing & Event Handling
// ============================================================================

// Canvas and context initialization
const canvas = document.getElementById('drawing-canvas');
const ctx = canvas.getContext('2d');

// Global project variable
let currentProject = null;

// ============================================================================
// HiDPI Canvas Setup
// ============================================================================

(function setupHiDPI() {
  const ratio = window.devicePixelRatio || 1;
  if (ratio !== 1) {
    const w = canvas.width;
    const h = canvas.height;
    canvas.width = Math.round(w * ratio);
    canvas.height = Math.round(h * ratio);
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
})();

// ============================================================================
// Application State
// ============================================================================

let currentTool = 'rectangle';
let currentColor = document.getElementById('drawing-color').value;
let lineWidth = parseInt(document.getElementById('line-width').value, 10);

let drawings = [];
let selectedIndex = -1;
let mode = 'idle'; // 'idle', 'drawing', 'moving', 'resizing'
let dragStart = null;
let resizeHandle = null;
let currentPath = null;
let tempShape = null;

// ============================================================================
// Toolbar Event Handlers
// ============================================================================

document.querySelectorAll('.btn[data-tool]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.btn[data-tool]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentTool = btn.getAttribute('data-tool');
    mode = 'idle';
    currentPath = null;
    tempShape = null;
    selectedIndex = -1;
    redraw();
  });
});

document.getElementById('drawing-color').addEventListener('input', e => {
  currentColor = e.target.value;
});

document.getElementById('line-width').addEventListener('input', e => {
  lineWidth = parseInt(e.target.value, 10);
});

// ============================================================================
// Coordinate Conversion
// ============================================================================

function toCanvasCoords(e) {
  const rect = canvas.getBoundingClientRect();
  const clientX = e.clientX ?? (e.touches && e.touches[0] && e.touches[0].clientX);
  const clientY = e.clientY ?? (e.touches && e.touches[0] && e.touches[0].clientY);
  return {
    x: clientX - rect.left,
    y: clientY - rect.top
  };
}

// ============================================================================
// Drawing Functions
// ============================================================================

function redraw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Draw all saved shapes
  drawings.forEach((d, i) => {
    if (i === selectedIndex) {
      ctx.save();
      ctx.globalAlpha = 0.7;
      drawShape(ctx, d);
      ctx.restore();
    } else {
      drawShape(ctx, d);
    }
  });
  
  // Draw temporary shape
  if (tempShape) {
    ctx.save();
    ctx.setLineDash([5, 5]);
    drawShape(ctx, tempShape);
    ctx.restore();
  }
  
  // ===== Enhanced selection box + handles =====
  if (selectedIndex >= 0 && mode === 'idle') {
    const s = drawings[selectedIndex];
    const b = getBounds(s);

    ctx.save();
    ctx.strokeStyle = "#2980b9";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 4]);
    ctx.strokeRect(b.x, b.y, b.w, b.h);
    ctx.restore();

    const handles = getHandles(s);
    ctx.fillStyle = "#3498db";
    handles.forEach(h => {
      ctx.beginPath();
      ctx.arc(h.x, h.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });

    s._handles = handles;
  }
}

function finalizeTempShape(shape) {
  if (shape) {
    drawings.push(shape);
  }
}

// ============================================================================
// Canvas Mouse Events
// ============================================================================

canvas.addEventListener('mousedown', (ev) => {
    // -------- TEXT TOOL ----------
  if (currentTool === 'text') {
    ev.preventDefault();
    ev.stopPropagation();

    const p = toCanvasCoords(ev);
    const rect = canvas.getBoundingClientRect();

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Enter text...";
    input.style.position = "absolute";
    input.style.left = (window.scrollX + rect.left + p.x) + "px";
    input.style.top  = (window.scrollY + rect.top  + p.y - 10) + "px";
    input.style.zIndex = "9999";
    input.style.fontSize = "18px";
    input.style.padding = "2px 4px";
    input.style.border = "1px solid #333";
    input.style.background = "white";

    document.body.appendChild(input);

    setTimeout(() => {
      input.focus();
    }, 0);

    const commit = () => {
      const text = input.value.trim();
      input.remove();
      if (!text) return;

      drawings.push({
        type: 'text',
        text,
        x: p.x,
        y: p.y,
        color: currentColor,
        fontSize: 18,
        strokeWidth: 1
      });
      redraw();
    };

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        commit();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        input.remove();
      }
    });

    setTimeout(() => {
      input.addEventListener('blur', commit);
    }, 0);

    return;
  }

  // -------- CURSOR TOOL ----------
  if (currentTool === 'cursor') {
    const p = toCanvasCoords(ev);
    const x = p.x, y = p.y;

    if (selectedIndex >= 0) {
      const s = drawings[selectedIndex];
      const handles = getHandles(s);
      for (let h of handles) {
        if (Math.hypot(x - h.x, y - h.y) < 8) {
          mode = 'resizing';
          resizeHandle = h.id;
          dragStart = {x, y};
          s._orig = JSON.parse(JSON.stringify(s));
          return;
        }
      }
    }

    for (let i = drawings.length - 1; i >= 0; i--) {
      if (hitTestShape(drawings[i], x, y)) {
        selectedIndex = i;
        mode = 'moving';
        dragStart = {x, y};
        drawings[i]._orig = JSON.parse(JSON.stringify(drawings[i]));
        redraw();
        return;
      }
    }

    selectedIndex = -1;
    mode = 'idle';
    redraw();
    return;
  }



  const p = toCanvasCoords(ev);
  const x = p.x;
  const y = p.y;
  
  // Check for handle hit
  if (selectedIndex >= 0) {
    const s = drawings[selectedIndex];
    const handles = getHandles(s);
    for (let h of handles) {
      if (Math.hypot(x - h.x, y - h.y) < 8) {
        mode = 'resizing';
        resizeHandle = h.id;
        dragStart = {x, y};
        s._orig = JSON.parse(JSON.stringify(s));
        return;
      }
    }
  }
  
  // Check for shape hit
  for (let i = drawings.length - 1; i >= 0; i--) {
    if (hitTestShape(drawings[i], x, y)) {
      selectedIndex = i;
      mode = 'moving';
      dragStart = {x, y};
      drawings[i]._orig = JSON.parse(JSON.stringify(drawings[i]));
      redraw();
      return;
    }
  }
  
  // Start new drawing
  selectedIndex = -1;
  mode = 'drawing';

  if (currentTool === 'eraser') {
    // start erase mode (no path)
    mode = 'drawing';
    selectedIndex = -1;
    dragStart = null;
    return;
  } else {
    // Create temporary shape
    tempShape = {
      type: currentTool === 'arrow' ? 'arrow' : 
            currentTool === 'line' ? 'line' :
            currentTool === 'rectangle' ? 'rectangle' :
            currentTool === 'ellipse' ? 'ellipse' :
            currentTool === 'triangle' ? 'triangle' : 'line',
      color: currentColor,
      strokeWidth: lineWidth,
      fill: 'none',
      x1: x, y1: y, x2: x, y2: y,
      x: x, y: y,
      rectWidth: 0, rectHeight: 0,
      cx: x, cy: y, rx: 0, ry: 0,
      radius: 0,
      points: currentTool === 'arrow' || currentTool === 'line' ? [{x: x, y: y}, {x: x, y: y}] : undefined,
      arrowheadType: currentTool === 'arrow' ? 'triangle' : undefined,
      arrowheadSize: currentTool === 'arrow' ? Math.max(10, lineWidth * 3) : undefined,
      arrowStart: currentTool === 'arrow' ? 'no' : undefined,
      arrowEnd: currentTool === 'arrow' ? 'yes' : undefined
    };
  }
  
  redraw();
});

canvas.addEventListener('mousemove', (ev) => {
  if (currentTool === 'eraser' && mode === 'drawing') {
    const p = toCanvasCoords(ev);
    for (let i = drawings.length - 1; i >= 0; i--) {
      if (hitTestShape(drawings[i], p.x, p.y)) {
        drawings.splice(i, 1);
        redraw();
        return;
      }
    }
  }
  
  const p = toCanvasCoords(ev);
  const x = p.x;
  const y = p.y;
  
  if (mode === 'drawing') {
    if (tempShape) {
      // Update temporary shape
      if (tempShape.type === 'line' || tempShape.type === 'arrow') {
        tempShape.x2 = x;
        tempShape.y2 = y;
        tempShape.points = [{x: tempShape.x1, y: tempShape.y1}, {x: tempShape.x2, y: tempShape.y2}];
      } else if (tempShape.type === 'rectangle') {
        tempShape.rectWidth = x - tempShape.x;
        tempShape.rectHeight = y - tempShape.y;
      } else if (tempShape.type === 'ellipse') {
        tempShape.rx = Math.abs(x - tempShape.cx);
        tempShape.ry = Math.abs(y - tempShape.cy);
      } else if (tempShape.type === 'circle') {
        tempShape.radius = Math.hypot(x - tempShape.x, y - tempShape.y);
      } else if (tempShape.type === 'triangle') {
        tempShape.x2 = x;
        tempShape.y2 = y;
      }
      redraw();
    }
  } else if (mode === 'moving' && selectedIndex >= 0 && dragStart) {
    const dx = x - dragStart.x;
    const dy = y - dragStart.y;
    const s = drawings[selectedIndex];
    const orig = s._orig;
    
    if (s.type === 'path') {
      s.points = orig.points.map(pt => ({x: pt.x + dx, y: pt.y + dy}));
    } else if (s.type === 'line' || s.type === 'arrow') {
      if (orig.points && orig.points.length > 1) {
        s.points = orig.points.map(pt => ({ x: pt.x + dx, y: pt.y + dy }));
      } else {
        s.x1 = orig.x1 + dx;
        s.y1 = orig.y1 + dy;
        s.x2 = orig.x2 + dx;
        s.y2 = orig.y2 + dy;
      }
    } else if (s.type === 'rectangle') {
      s.x = orig.x + dx;
      s.y = orig.y + dy;
    } else if (s.type === 'circle') {
      s.x = orig.x + dx;
      s.y = orig.y + dy;
    } else if (s.type === 'ellipse') {
      s.cx = orig.cx + dx;
      s.cy = orig.cy + dy;
    } else if (s.type === 'triangle') {
      s.x1 = orig.x1 + dx;
      s.y1 = orig.y1 + dy;
      s.x2 = orig.x2 + dx;
      s.y2 = orig.y2 + dy;
    } else if (s.type === 'text') {
      s.x = orig.x + dx;
      s.y = orig.y + dy;
    }
    
    redraw();
  } else if (mode === 'resizing' && selectedIndex >= 0 && dragStart && resizeHandle) {
    const dx = x - dragStart.x;
    const dy = y - dragStart.y;
    const s = drawings[selectedIndex];
    const orig = s._orig;

    if (s.type === 'line' || s.type === 'arrow') {
      if (orig.points && orig.points.length > 1) {
        const newPts = orig.points.map(p => ({ ...p }));

        if (resizeHandle === 'p1') {
          newPts[0] = {
            x: orig.points[0].x + dx,
            y: orig.points[0].y + dy
          };
        } else if (resizeHandle === 'p2') {
          const L = orig.points.length - 1;
          newPts[L] = {
            x: orig.points[L].x + dx,
            y: orig.points[L].y + dy
          };
        } else if (resizeHandle && resizeHandle.startsWith('mid_')) {
          const index = parseInt(resizeHandle.split('_')[1], 10); // 1..L-1
          newPts[index] = {
            x: orig.points[index].x + dx,
            y: orig.points[index].y + dy
          };
        }

        s.points = newPts;
      } else {
        if (resizeHandle === 'p1') {
          s.x1 = orig.x1 + dx;
          s.y1 = orig.y1 + dy;
        } else if (resizeHandle === 'p2') {
          s.x2 = orig.x2 + dx;
          s.y2 = orig.y2 + dy;
        }
      }
    } else if (s.type === 'circle') {
      if (resizeHandle === 'r') {
        s.radius = Math.hypot(x - s.x, y - s.y);
      }
    }

    else if (s.type === 'rectangle') {
      let x0 = orig.x, y0 = orig.y, w0 = orig.rectWidth, h0 = orig.rectHeight;

      const applyCorner = (left, top, right, bottom) => {
        let x = x0, y = y0, w = w0, h = h0;

        if (left)  { x = orig.x + dx; w = orig.rectWidth - dx; }
        if (top)   { y = orig.y + dy; h = orig.rectHeight - dy; }
        if (right) { w = orig.rectWidth + dx; }
        if (bottom){ h = orig.rectHeight + dy; }

        s.x = x;
        s.y = y;
        s.rectWidth  = w;
        s.rectHeight = h;
      };

      switch (resizeHandle) {
        case 'tl': applyCorner(1,1,0,0); break;
        case 'tr': applyCorner(0,1,1,0); break;
        case 'bl': applyCorner(1,0,0,1); break;
        case 'br': applyCorner(0,0,1,1); break;
        case 'tm': applyCorner(0,1,0,0); break;
        case 'bm': applyCorner(0,0,0,1); break;
        case 'ml': applyCorner(1,0,0,0); break;
        case 'mr': applyCorner(0,0,1,0); break;
      }
    }

    else if (s.type === 'ellipse') {
      let bx = orig.cx - orig.rx;
      let by = orig.cy - orig.ry;
      let bw = orig.rx * 2;
      let bh = orig.ry * 2;

      const applyCorner = (left, top, right, bottom) => {
        let x_ = bx, y_ = by, w_ = bw, h_ = bh;

        if (left)  { x_ = bx + dx; w_ = bw - dx; }
        if (top)   { y_ = by + dy; h_ = bh - dy; }
        if (right) { w_ = bw + dx; }
        if (bottom){ h_ = bh + dy; }

        s.cx = x_ + w_ / 2;
        s.cy = y_ + h_ / 2;
        s.rx = Math.abs(w_ / 2);
        s.ry = Math.abs(h_ / 2);
      };

      switch (resizeHandle) {
        case 'tl': applyCorner(1,1,0,0); break;
        case 'tr': applyCorner(0,1,1,0); break;
        case 'bl': applyCorner(1,0,0,1); break;
        case 'br': applyCorner(0,0,1,1); break;
        case 'tm': applyCorner(0,1,0,0); break;
        case 'bm': applyCorner(0,0,0,1); break;
        case 'ml': applyCorner(1,0,0,0); break;
        case 'mr': applyCorner(0,0,1,0); break;
      }
    }

    else if (s.type === 'triangle') {
      const minX = Math.min(orig.x1, orig.x2);
      const minY = Math.min(orig.y1, orig.y2);
      const maxX = Math.max(orig.x1, orig.x2);
      const maxY = Math.max(orig.y1, orig.y2);

      let x_ = minX, y_ = minY, w_ = maxX - minX, h_ = maxY - minY;

      const applyCorner = (left, top, right, bottom) => {
        if (left)  { x_ = minX + dx; w_ = (maxX - minX) - dx; }
        if (top)   { y_ = minY + dy; h_ = (maxY - minY) - dy; }
        if (right) { w_ = (maxX - minX) + dx; }
        if (bottom){ h_ = (maxY - minY) + dy; }

        s.x1 = x_;
        s.y1 = y_;
        s.x2 = x_ + w_;
        s.y2 = y_ + h_;
      };

      switch (resizeHandle) {
        case 'tl': applyCorner(1,1,0,0); break;
        case 'tr': applyCorner(0,1,1,0); break;
        case 'bl': applyCorner(1,0,0,1); break;
        case 'br': applyCorner(0,0,1,1); break;
        case 'tm': applyCorner(0,1,0,0); break;
        case 'bm': applyCorner(0,0,0,1); break;
        case 'ml': applyCorner(1,0,0,0); break;
        case 'mr': applyCorner(0,0,1,0); break;
      }
    }

    else if (s.type === 'text') {
      const newSize = Math.max(8, (orig.fontSize || 18) + dy * 0.3);
      s.fontSize = newSize;
    }

    redraw();
  }
  
  // Update cursor
  let cursor = 'default';
  if (currentTool === 'cursor') {
    if (mode === 'moving') cursor = 'move';
    else if (mode === 'resizing') cursor = 'nwse-resize';
    else if (selectedIndex >= 0) {
      const s = drawings[selectedIndex];
      const handles = getHandles(s);
      for (let h of handles) {
        if (Math.hypot(x - h.x, y - h.y) < 8) {
          cursor = 'nwse-resize';
          break;
        }
      }
      if (cursor === 'default' && hitTestShape(s, x, y)) cursor = 'move';
    }
    canvas.style.cursor = cursor;
    return;
  } else if (mode === 'moving') {
    cursor = 'move';
  } else if (mode === 'resizing') {
    cursor = 'nwse-resize';
  } else if (selectedIndex >= 0) {
    const s = drawings[selectedIndex];
    const handles = getHandles(s);
    for (let h of handles) {
      if (Math.hypot(x - h.x, y - h.y) < 8) {
        cursor = 'pointer';
        break;
      }
    }
    if (cursor === 'default' && hitTestShape(s, x, y)) {
      cursor = 'move';
    }
  } else {
    for (let i = drawings.length - 1; i >= 0; i--) {
      if (hitTestShape(drawings[i], x, y)) {
        cursor = 'pointer';
        break;
      }
    }
  }
  canvas.style.cursor = cursor;
});

canvas.addEventListener('mouseup', (ev) => {
  const p = toCanvasCoords(ev);
  const x = p.x;
  const y = p.y;
  
  if (mode === 'drawing') {
    if (currentTool !== 'draw' && currentTool !== 'eraser' && tempShape) {
      if (tempShape) {
        const MIN_SIZE = 8;

        if (tempShape.type === "rectangle") {
          if (Math.abs(tempShape.rectWidth) < MIN_SIZE)
            tempShape.rectWidth = tempShape.rectWidth < 0 ? -MIN_SIZE : MIN_SIZE;
          if (Math.abs(tempShape.rectHeight) < MIN_SIZE)
            tempShape.rectHeight = tempShape.rectHeight < 0 ? -MIN_SIZE : MIN_SIZE;
        }

        if (tempShape.type === "ellipse") {
          if (tempShape.rx < MIN_SIZE) tempShape.rx = MIN_SIZE;
          if (tempShape.ry < MIN_SIZE) tempShape.ry = MIN_SIZE;
        }

        if (tempShape.type === "circle") {
          if (tempShape.radius < MIN_SIZE) tempShape.radius = MIN_SIZE;
        }

        if (tempShape.type === "triangle") {
          const w = Math.abs(tempShape.x2 - tempShape.x1);
          const h = Math.abs(tempShape.y2 - tempShape.y1);
          if (w < MIN_SIZE) {
            if (tempShape.x2 > tempShape.x1) tempShape.x2 = tempShape.x1 + MIN_SIZE;
            else tempShape.x2 = tempShape.x1 - MIN_SIZE;
          }
          if (h < MIN_SIZE) {
            if (tempShape.y2 > tempShape.y1) tempShape.y2 = tempShape.y1 + MIN_SIZE;
            else tempShape.y2 = tempShape.y1 - MIN_SIZE;
          }
        }
      }
      finalizeTempShape(tempShape);
      tempShape = null;
    }
    currentPath = null;
    mode = 'idle';
    redraw();
    return;
  }
  
  if (mode === 'moving') {
    if (selectedIndex >= 0 && drawings[selectedIndex]._orig) {
      delete drawings[selectedIndex]._orig;
    }
    mode = 'idle';
    dragStart = null;
    return;
  }
  
  if (mode === 'resizing') {
    if (selectedIndex >= 0 && drawings[selectedIndex]._orig) {
      delete drawings[selectedIndex]._orig;
    }
    resizeHandle = null;
    mode = 'idle';
    dragStart = null;
    return;
  }

  if (currentTool === 'cursor') {
    mode = 'idle';
    dragStart = null;
    resizeHandle = null;
    return;
  }
});

canvas.addEventListener('mouseleave', () => {
  if (mode === 'drawing') {
    currentPath = null;
    mode = 'idle';
  }
});

// ============================================================================
// Keyboard Events
// ============================================================================

document.addEventListener('keydown', (e) => {
  if ((e.key === 'Delete' || e.key === 'Backspace') && selectedIndex >= 0) {
    drawings.splice(selectedIndex, 1);
    selectedIndex = -1;
    redraw();
  }
});

// ============================================================================
// Mouse Wheel for Scaling
// ============================================================================

canvas.addEventListener('wheel', (e) => {
  if (selectedIndex >= 0) {
    const s = drawings[selectedIndex];
    const scale = e.deltaY < 0 ? 1.05 : 0.95;
    
    if (s.type === 'rectangle') {
      s.rectWidth *= scale;
      s.rectHeight *= scale;
    } else if (s.type === 'ellipse') {
      s.rx *= scale;
      s.ry *= scale;
    } else if (s.type === 'circle') {
      s.radius *= scale;
    }
    
    redraw();
    e.preventDefault();
  }
});

// ============================================================================
// Action Button Handlers
// ============================================================================

// ============================================================================
// Generate JSON + Preview 
// ============================================================================
document.getElementById('generate-btn').addEventListener('click', async () => {
  // ===== Update SVG preview from JSON data =====
  const jsonDict = drawingsToJsonDict(drawings);
  const jsonText = JSON.stringify(jsonDict, null, 2);
  document.getElementById('json-code').value = jsonText;

  await updateSVGPreview(jsonDict);
});
  /**
   * Update SVG preview from JSON data
   */
async function updateSVGPreview(jsonDict) {
  // Try to call Python backend to generate SVG
  // ===== Update SVG preview from JSON data =====
  try {
    const response = await fetch('http://localhost:8080/json-to-svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        shapes: jsonDict,
        width: 800,
        height: 600,
        background: 'white'
      })
    });

    const data = await response.json();

    if (data.success) {
      // get svg from backend
      console.log('SVG generated by backend');
      document.getElementById('svg-preview').innerHTML = data.svg;
      // console.log('SVG from backend:', data.svg);
    } else {
      // Fallback to client-side generation
      console.log('Backend SVG generation failed, using client-side SVG generation');
      const svg = generateSVGFromJson(jsonDict, 800, 600);
      document.getElementById('svg-preview').innerHTML = svg;
    }
  } catch (error) {
    // Fallback to client-side SVG generation
    // console.log('Backend unavailable, using client-side SVG generation');
    const svg = generateSVGFromJson(jsonDict, 800, 600);
    document.getElementById('svg-preview').innerHTML = svg;
  }
}

// ============================================================================
// JSON Textarea Change Handler
// ============================================================================

let jsonUpdateTimeout = null;
const jsonCodeArea = document.getElementById('json-code');
const jsonStatus = document.getElementById('json-status');

document.getElementById('json-code').addEventListener('input', (e) => {
  // Debounce the update to avoid excessive processing
  clearTimeout(jsonUpdateTimeout);
  
  // Remove previous validation classes
  jsonCodeArea.classList.remove('valid', 'invalid');
  jsonStatus.textContent = 'Parsing...';
  jsonStatus.className = 'json-status';
  
  jsonUpdateTimeout = setTimeout(async () => {
    const jsonText = e.target.value.trim();
    
    if (!jsonText) {
      // Clear everything if JSON is empty
      drawings = [];
      selectedIndex = -1;
      redraw();
      document.getElementById('svg-preview').innerHTML = '<p style="text-align:center;margin-top:60px">SVG preview will appear here</p>';
      jsonStatus.textContent = '';
      jsonCodeArea.classList.remove('valid', 'invalid');
      return;
    }
    
    try {
      // Parse JSON
      const jsonDict = JSON.parse(jsonText);
      
      // Validate it's an array
      if (!Array.isArray(jsonDict)) {
        throw new Error('JSON must be an array of shapes');
      }
      
      // Convert JSON to drawings
      drawings = jsonDictToDrawings(jsonDict);
      selectedIndex = -1;
      
      // Update canvas
      redraw();
      
      // Update SVG preview
      await updateSVGPreview(jsonDict);
      
      // Show success
      jsonCodeArea.classList.add('valid');
      jsonStatus.textContent = `✓ Valid JSON `;
      jsonStatus.className = 'json-status valid';
      
    } catch (error) {
      // Show error
      jsonCodeArea.classList.add('invalid');
      jsonStatus.textContent = `✗ Invalid JSON: ${error.message}`;
      jsonStatus.className = 'json-status invalid';
      console.error('JSON Parse Error:', error);
    }
  }, 500); // Wait 500ms after user stops typing
});


document.getElementById('download-btn').addEventListener('click', () => {
  const svg = document.getElementById('svg-preview').innerHTML;
  if (!svg || svg.includes('SVG preview will appear here')) {
    alert('Please generate SVG first');
    return;
  }
  
  const blob = new Blob([svg], {type: 'image/svg+xml'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'flowchart.svg';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

document.getElementById('clear-btn').addEventListener('click', () => {
  drawings = [];
  selectedIndex = -1;
  mode = 'idle';
  tempShape = null;
  currentPath = null;
  redraw();
  document.getElementById('json-code').value = '';
  document.getElementById('svg-preview').innerHTML = '<p style="text-align:center;margin-top:60px">SVG preview will appear here</p>';
});

// ============================================================================
// Initialize
// ============================================================================
redraw();
