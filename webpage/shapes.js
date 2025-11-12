// ============================================================================
// Shape Utility Functions
// ============================================================================
function drawArrowHead(ctx, x1, y1, x2, y2) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const size = 10;
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - size * Math.cos(angle - Math.PI / 6),
             y2 - size * Math.sin(angle - Math.PI / 6));
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - size * Math.cos(angle + Math.PI / 6),
             y2 - size * Math.sin(angle + Math.PI / 6));
  ctx.stroke();
}

/**
 * Calculate distance from point to line segment
 */
function pointToSegmentDistance(p, a, b) {
  const A = p.x - a.x;
  const B = p.y - a.y;
  const C = b.x - a.x;
  const D = b.y - a.y;
  const dot = A * C + B * D;
  const len_sq = C * C + D * D;
  let param = len_sq !== 0 ? dot / len_sq : -1;
  let xx, yy;
  
  if (param < 0) {
    xx = a.x;
    yy = a.y;
  } else if (param > 1) {
    xx = b.x;
    yy = b.y;
  } else {
    xx = a.x + param * C;
    yy = a.y + param * D;
  }
  
  return Math.hypot(p.x - xx, p.y - yy);
}

/**
 * Check if point is inside rectangle
 */
function pointInRect(x, y, rx, ry, rw, rh) {
  return x >= rx && x <= rx + rw && y >= ry && y <= ry + rh;
}

/**
 * Check if point is inside polygon using ray casting
 */
function pointInPolygon(pt, vs) {
  let x = pt.x;
  let y = pt.y;
  let inside = false;
  
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const xi = vs[i].x;
    const yi = vs[i].y;
    const xj = vs[j].x;
    const yj = vs[j].y;
    
    if ((yi > y) !== (yj > y)) {
      if (x < (xj - xi) * (y - yi) / (yj - yi) + xi) {
        inside = !inside;
      }
    }
  }
  
  return inside;
}

/**
 * Hit test for shapes - determines if a point hits a shape
 */
function hitTestShape(shape, x, y) {
  const thresh = 10;
  const MIN_SIZE = 8;

  if (shape.type === 'path') {
    if (!shape.points || shape.points.length < 2) return false;
    for (let i = 0; i < shape.points.length - 1; i++) {
      if (pointToSegmentDistance({ x, y }, shape.points[i], shape.points[i + 1]) < thresh) {
        return true;
      }
    }
    return false;
  }

  if (shape.type === 'line') {
    return pointToSegmentDistance(
      { x, y },
      { x: shape.x1, y: shape.y1 },
      { x: shape.x2, y: shape.y2 }
    ) < thresh;
  }

  if (shape.type === 'arrow') {
    if (shape.points && shape.points.length > 1) {
      for (let i = 0; i < shape.points.length - 1; i++) {
        if (pointToSegmentDistance({ x, y }, shape.points[i], shape.points[i + 1]) < thresh) return true;
      }
      return false;
    }
    return pointToSegmentDistance(
      { x, y },
      { x: shape.x1, y: shape.y1 },
      { x: shape.x2, y: shape.y2 }
    ) < thresh;
  }

  if (shape.type === "rectangle") {
    const w = Math.abs(shape.rectWidth);
    const h = Math.abs(shape.rectHeight);
    if (w < MIN_SIZE && h < MIN_SIZE) {
      return (
        x >= shape.x &&
        x <= shape.x + w &&
        y >= shape.y &&
        y <= shape.y + h
      );
    }
    const left = shape.x;
    const right = shape.x + shape.rectWidth;
    const top = shape.y;
    const bottom = shape.y + shape.rectHeight;
    const nearLeft = Math.abs(x - left) < thresh && y >= top && y <= bottom;
    const nearRight = Math.abs(x - right) < thresh && y >= top && y <= bottom;
    const nearTop = Math.abs(y - top) < thresh && x >= left && x <= right;
    const nearBottom = Math.abs(y - bottom) < thresh && x >= left && x <= right;
    return nearLeft || nearRight || nearTop || nearBottom;
  }

  if (shape.type === "circle") {
    const dist = Math.hypot(x - shape.x, y - shape.y);
    if (shape.radius < MIN_SIZE) {
      return dist <= shape.radius + 2;
    }
    const diff = Math.abs(dist - shape.radius);
    return diff < thresh;
  }

  if (shape.type === "ellipse") {
    const dx = x - shape.cx;
    const dy = y - shape.cy;
    if (shape.rx < MIN_SIZE && shape.ry < MIN_SIZE) {
      return Math.hypot(dx, dy) < MIN_SIZE;
    }
    const v = (dx * dx) / (shape.rx * shape.rx) + (dy * dy) / (shape.ry * shape.ry);
    return Math.abs(v - 1) < 0.2;
  }

  if (shape.type === "triangle") {
    const w = Math.abs(shape.x2 - shape.x1);
    const h = Math.abs(shape.y2 - shape.y1);
    const cx = (shape.x1 + shape.x2) / 2;
    const pts = [
      { x: cx, y: shape.y1 },
      { x: shape.x1, y: shape.y2 },
      { x: shape.x2, y: shape.y2 }
    ];
    const p = { x, y };
    if (w < MIN_SIZE && h < MIN_SIZE) {
      return pointInPolygon(p, pts);
    }
    const d1 = pointToSegmentDistance(p, pts[0], pts[1]);
    const d2 = pointToSegmentDistance(p, pts[1], pts[2]);
    const d3 = pointToSegmentDistance(p, pts[2], pts[0]);
    return d1 < thresh || d2 < thresh || d3 < thresh;
  }

  if (shape.type === 'text') {
    const fontSize = shape.fontSize || 18;
    ctx.font = `${fontSize}px Arial`;
    const width = ctx.measureText(shape.text).width;
    return (
      x >= shape.x &&
      x <= shape.x + width &&
      y <= shape.y &&
      y >= shape.y - fontSize
    );
  }

  return false;
}

/**
 * Get bounding box for a shape
 */
function getBounds(s) {
  if (s.type === 'path') {
    if (!s.points || s.points.length === 0) return {x: 0, y: 0, w: 0, h: 0};
    const xs = s.points.map(p => p.x);
    const ys = s.points.map(p => p.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);
    return {x: minX, y: minY, w: maxX - minX, h: maxY - minY};
  }
  
  if (s.type === 'line' || s.type === 'arrow') {
    if (s.points && s.points.length > 1) {
      const xs = s.points.map(p => p.x);
      const ys = s.points.map(p => p.y);
      const minX = Math.min(...xs);
      const minY = Math.min(...ys);
      const maxX = Math.max(...xs);
      const maxY = Math.max(...ys);
      return {x: minX, y: minY, w: maxX - minX, h: maxY - minY};
    } else {
      const minX = Math.min(s.x1, s.x2);
      const minY = Math.min(s.y1, s.y2);
      const maxX = Math.max(s.x1, s.x2);
      const maxY = Math.max(s.y1, s.y2);
      return {x: minX, y: minY, w: maxX - minX, h: maxY - minY};
    }
  }
  
  if (s.type === 'rectangle') {
    return {x: s.x, y: s.y, w: s.rectWidth, h: s.rectHeight};
  }
  
  if (s.type === 'circle') {
    return {x: s.x - s.radius, y: s.y - s.radius, w: s.radius * 2, h: s.radius * 2};
  }
  
  if (s.type === 'ellipse') {
    return {x: s.cx - s.rx, y: s.cy - s.ry, w: s.rx * 2, h: s.ry * 2};
  }
  
  if (s.type === 'triangle') {
    const minX = Math.min(s.x1, s.x2);
    const minY = Math.min(s.y1, s.y2);
    const maxX = Math.max(s.x1, s.x2);
    const maxY = Math.max(s.y1, s.y2);
    return {x: minX, y: minY, w: maxX - minX, h: maxY - minY};
  }
  // --- add: bounds for text ---
  if (s.type === 'text') {
    const fontSize = s.fontSize || 18;
    ctx.font = `${fontSize}px Arial`;
    const width = ctx.measureText(s.text || '').width;
    return { x: s.x, y: s.y - fontSize, w: width, h: fontSize };
  }
  
  return {x: 0, y: 0, w: 0, h: 0};
}

/**
 * Get resize handles for selected shape
 */
function getHandles(s) {
  const b = getBounds(s);
  const handles = [];

  const eight = [
    { id: 'tl', x: b.x,           y: b.y           },
    { id: 'tm', x: b.x + b.w / 2, y: b.y           },
    { id: 'tr', x: b.x + b.w,     y: b.y           },
    { id: 'ml', x: b.x,           y: b.y + b.h / 2 },
    { id: 'mr', x: b.x + b.w,     y: b.y + b.h / 2 },
    { id: 'bl', x: b.x,           y: b.y + b.h     },
    { id: 'bm', x: b.x + b.w / 2, y: b.y + b.h     },
    { id: 'br', x: b.x + b.w,     y: b.y + b.h     },
  ];

  if (s.type === 'rectangle' || s.type === 'ellipse' || s.type === 'triangle' || s.type === 'text') {
    return eight;
  } else if (s.type === 'line' || s.type === 'arrow') {
    if (s.points && s.points.length > 1) {
      const handles = [];

      handles.push({ id: 'p1', x: s.points[0].x, y: s.points[0].y });

      for (let i = 1; i < s.points.length - 1; i++) {
        handles.push({ id: 'mid_' + i, x: s.points[i].x, y: s.points[i].y });
      }

      const last = s.points.length - 1;
      handles.push({ id: 'p2', x: s.points[last].x, y: s.points[last].y });

      return handles;
    }
    return [
      { id: 'p1', x: s.x1, y: s.y1 },
      { id: 'p2', x: s.x2, y: s.y2 },
    ];
  } else if (s.type === 'circle') {
    return [{ id: 'r', x: s.x + s.radius, y: s.y }];
  }
  return handles;
}

/**
 * Draw a single shape on canvas
 */
function drawShape(ctx, s) {
  ctx.strokeStyle = s.color || '#000';
  ctx.lineWidth = s.strokeWidth || 1;
  ctx.fillStyle = s.fill || 'none';
  
  if (s.type === 'path') {
    if (!s.points || s.points.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(s.points[0].x, s.points[0].y);
    for (let i = 1; i < s.points.length; i++) {
      ctx.lineTo(s.points[i].x, s.points[i].y);
    }
    ctx.stroke();
  } else if (s.type === 'line') {
    ctx.beginPath();
    ctx.moveTo(s.x1, s.y1);
    ctx.lineTo(s.x2, s.y2);
    ctx.stroke();
  } else if (s.type === 'arrow') {
    ctx.strokeStyle = s.color || '#2c3e50';
    ctx.lineWidth = s.strokeWidth || 3;
    ctx.beginPath();

    if (s.points && s.points.length > 1) {
      ctx.moveTo(s.points[0].x, s.points[0].y);
      for (let i = 1; i < s.points.length; i++) {
        ctx.lineTo(s.points[i].x, s.points[i].y);
      }
      ctx.stroke();

      const L = s.points.length;
      drawArrowHead(ctx,
        s.points[L-2].x, s.points[L-2].y,
        s.points[L-1].x, s.points[L-1].y
      );
    } else {
      ctx.moveTo(s.x1, s.y1);
      ctx.lineTo(s.x2, s.y2);
      ctx.stroke();

      drawArrowHead(ctx, s.x1, s.y1, s.x2, s.y2);
    }
  } else if (s.type === 'rectangle') {
    if (s.fill && s.fill !== 'none') {
      ctx.fillRect(s.x, s.y, s.rectWidth, s.rectHeight);
    }
    ctx.strokeRect(s.x, s.y, s.rectWidth, s.rectHeight);
  } else if (s.type === 'circle') {
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
    if (s.fill && s.fill !== 'none') {
      ctx.fill();
    }
    ctx.stroke();
  } else if (s.type === 'ellipse') {
    ctx.beginPath();
    ctx.ellipse(s.cx, s.cy, s.rx, s.ry, 0, 0, Math.PI * 2);
    if (s.fill && s.fill !== 'none') {
      ctx.fill();
    }
    ctx.stroke();
  } else if (s.type === 'triangle') {
    const cx = (s.x1 + s.x2) / 2;
    ctx.beginPath();
    ctx.moveTo(cx, s.y1);
    ctx.lineTo(s.x1, s.y2);
    ctx.lineTo(s.x2, s.y2);
    ctx.closePath();
    if (s.fill && s.fill !== 'none') {
      ctx.fill();
    }
    ctx.stroke();
  } else if (s.type === 'text') {
    ctx.fillStyle = s.color || '#000';
    ctx.font = `${s.fontSize || 18}px Arial`;
    ctx.fillText(s.text, s.x, s.y);
  }
}
