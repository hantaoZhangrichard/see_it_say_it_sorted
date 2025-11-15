// ============================================================================
// JSON Dictionary Conversion Functions
// ============================================================================

/**
 * Convert canvas drawings to JSON dictionary format
 * This format is compatible with the Python backend
 */
function drawingsToJsonDict(drawings, srcWidth = 800, srcHeight = 600, tgtWidth = 600, tgtHeight = 450) {
  const scaleX = tgtWidth / srcWidth;
  const scaleY = tgtHeight / srcHeight;
  const shapes = [];
  const MIN_S = 8;

  drawings.forEach(d => {
    let shape = {
      shape_type: d.type,
      stroke_color: d.color || '#000000',
      stroke_width: (d.strokeWidth || 1) / ((scaleX + scaleY) / 2),
      fill_color: d.fill || 'none'
    };

    if (d.type === 'path') {
      shape.shape_type = 'polyline';
      shape.points = d.points.map(p => [p.x / scaleX, p.y / scaleY]);
    } else if (d.type === 'line') {
      shape.shape_type = 'polyline';
      shape.points = [[d.x1 / scaleX, d.y1 / scaleY], [d.x2 / scaleX, d.y2 / scaleY]];
    } else if (d.type === 'arrow') {
      shape.shape_type = 'arrow';
      if (d.points && d.points.length > 1) {
        shape.points = d.points.map(p => [p.x / scaleX, p.y / scaleY]);
      } else {
        shape.points = [[d.x1 / scaleX, d.y1 / scaleY], [d.x2 / scaleX, d.y2 / scaleY]];
      }
      shape.arrow_start = d.arrowStart || 'no';
      shape.arrow_end = d.arrowEnd || 'yes';
      shape.arrowhead_type = d.arrowheadType || 'triangle';
      shape.arrowhead_size = d.arrowheadSize / ((scaleX + scaleY) / 2) || 10;
    } else if (d.type === 'rectangle') {
      shape.shape_type = 'rectangle';
      shape.x = (d.x + d.rectWidth / 2) / scaleX;
      shape.y = (d.y + d.rectHeight / 2) / scaleY;
      shape.scale_x = d.rectWidth / scaleX;
      shape.scale_y = d.rectHeight / scaleY;
    } else if (d.type === 'circle') {
      shape.shape_type = 'circle';
      shape.x = d.x / scaleX;
      shape.y = d.y / scaleY;
      shape.scale_x = (d.radius * 2) / scaleX;
      shape.scale_y = (d.radius * 2) / scaleY;
    } else if (d.type === 'ellipse') {
      shape.shape_type = 'ellipse';
      shape.x = d.cx / scaleX;
      shape.y = d.cy / scaleY;
      shape.scale_x = (d.rx * 2) / scaleX;
      shape.scale_y = (d.ry * 2) / scaleY;
    } else if (d.type === 'triangle') {
      shape.shape_type = 'triangle';
      const cx = (d.x1 + d.x2) / 2;
      const cy = (d.y1 + d.y2) / 2;
      shape.x = cx / scaleX;
      shape.y = cy / scaleY;
      shape.scale_x = Math.abs(d.x2 - d.x1) / scaleX;
      shape.scale_y = Math.abs(d.y2 - d.y1) / scaleY;
    } else if (d.type === 'text') {
      shape.shape_type = 'text';
      shape.text = d.text;
      shape.x = d.x / scaleX;
      shape.y = d.y / scaleY;
      shape.font_size = (d.fontSize || 18) / ((scaleX + scaleY) / 2);
    }

    if (shape.scale_x !== undefined && Math.abs(shape.scale_x) < MIN_S) {
      shape.scale_x = shape.scale_x < 0 ? -MIN_S : MIN_S;
    }
    if (shape.scale_y !== undefined && Math.abs(shape.scale_y) < MIN_S) {
      shape.scale_y = shape.scale_y < 0 ? -MIN_S : MIN_S;
    }

    shapes.push(shape);
  });

  return shapes;
}

/**
 * Calculate triangle arrowhead points
 */
function arrowHeadPoints(x1, y1, x2, y2, headlen) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const angle = Math.atan2(dy, dx);
  
  const p1 = {x: x2, y: y2};
  const p2 = {
    x: x2 - headlen * Math.cos(angle - Math.PI / 6),
    y: y2 - headlen * Math.sin(angle - Math.PI / 6)
  };
  const p3 = {
    x: x2 - headlen * Math.cos(angle + Math.PI / 6),
    y: y2 - headlen * Math.sin(angle + Math.PI / 6)
  };
  
  return [p1, p2, p3];
}


/**
 * Convert JSON dictionary back to canvas drawings format
 */
function jsonDictToDrawings(shapes, srcWidth = 800, srcHeight = 600, tgtWidth = 600, tgtHeight = 450) {
  const scaleX = tgtWidth / srcWidth;
  const scaleY = tgtHeight / srcHeight;
  const drawings = [];
  
  shapes.forEach(shape => {
    let drawing = {
      color: shape.stroke_color || '#000000',
      strokeWidth: shape.stroke_width * scaleX || 1,
      fill: shape.fill_color || 'none'
    };
    
    if (shape.shape_type === 'polyline' && shape.points) {
      // Convert polyline to path
      drawing.type = 'path';
      drawing.points = shape.points.map(p => ({x: p[0] * scaleX, y: p[1] * scaleY}));
      
    } else if (shape.shape_type === 'arrow' && shape.points && shape.points.length >= 2) {
      drawing.type = 'arrow';

      drawing.points = shape.points.map(p => ({x: p[0] * scaleX, y: p[1] * scaleY}));

      drawing.arrowheadSize = shape.arrowhead_size * ((scaleX + scaleY) / 2);
      drawing.arrowStart = shape.arrow_start;
      drawing.arrowEnd = shape.arrow_end;
    } else if (shape.shape_type === 'rectangle') {
      drawing.type = 'rectangle';
      drawing.x = (shape.x - shape.scale_x / 2) * scaleX;
      drawing.y = (shape.y - shape.scale_y / 2) * scaleY;
      drawing.rectWidth = shape.scale_x * scaleX;
      drawing.rectHeight = shape.scale_y * scaleY;
      
    } else if (shape.shape_type === 'circle') {
      drawing.type = 'circle';
      drawing.x = shape.x * scaleX;
      drawing.y = shape.y * scaleY;
      drawing.radius = (shape.scale_x / 2) * scaleX;
      
    } else if (shape.shape_type === 'ellipse') {
      drawing.type = 'ellipse';
      drawing.cx = shape.x * scaleX;
      drawing.cy = shape.y * scaleY;
      drawing.rx = (shape.scale_x / 2) * scaleX;
      drawing.ry = (shape.scale_y / 2) * scaleY;
      
    } else if (shape.shape_type === 'triangle') {
      drawing.type = 'triangle';
      const w = shape.scale_x * scaleX;
      const h = shape.scale_y * scaleY;
      drawing.x1 = (shape.x - shape.scale_x / 2) * scaleX;
      drawing.y1 = (shape.y - shape.scale_y / 2) * scaleY;
      drawing.x2 = (shape.x + shape.scale_x / 2) * scaleX;
      drawing.y2 = (shape.y + shape.scale_y / 2) * scaleY;
    } else if (shape.shape_type === 'text') {
      drawing.type = 'text';
      drawing.text = shape.text;
      drawing.textColor = shape.text_color || '#000000';
      drawing.x = shape.x * scaleX;
      drawing.y = shape.y * scaleY;
      drawing.fontSize = shape.font_size * ((scaleX + scaleY) / 2) || 18;
      drawing.fontFamily = shape.font_family || 'Arial';
      drawing.textAnchor = shape.text_anchor || 'middle';
    }
    
    if (drawing.type) {
      drawings.push(drawing);
    }
  });
  
  return drawings;
}


/**
 * Generate SVG from JSON dictionary (if backend is unavailable)
 * This is a fallback client-side SVG generator
 */
function generateSVGFromJson(shapes, width = 800, height = 600) {
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="${width}" height="${height}" fill="white"/>`;
  
  shapes.forEach(shape => {
    const stroke = shape.stroke_color || '#000000';
    const strokeWidth = shape.stroke_width || 1;
    const fill = shape.fill_color || 'none';
    
    if (shape.shape_type === 'polyline' && shape.points) {
      const pointsStr = shape.points.map(p => `${p[0]},${p[1]}`).join(' ');
      svg += `<polyline points="${pointsStr}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="none"/>`;
      
    } else if (shape.shape_type === 'arrow' && shape.points && shape.points.length >= 2) {
      const stroke = shape.stroke_color || '#000000';
      const strokeWidth = shape.stroke_width || 1;

      if (shape.points.length > 2) {
        const pts = shape.points.map(p => `${p[0]},${p[1]}`).join(' ');
        const [x1, y1] = shape.points[shape.points.length - 2];
        const [x2, y2] = shape.points[shape.points.length - 1];
        const headlen = shape.arrowhead_size || 10;
        const ptsHead = arrowHeadPoints(x1, y1, x2, y2, headlen);
        svg += `<polyline points="${pts}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="none"/>`;
        svg += `<polygon points="${ptsHead[0].x},${ptsHead[0].y} ${ptsHead[1].x},${ptsHead[1].y} ${ptsHead[2].x},${ptsHead[2].y}" fill="${stroke}"/>`;
      } else {
        const [x1, y1] = shape.points[0];
        const [x2, y2] = shape.points[1];
        svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${strokeWidth}"/>`;
        if (shape.arrow_end === 'yes') {
          const headlen = shape.arrowhead_size || 10;
          const pts = arrowHeadPoints(x1, y1, x2, y2, headlen);
          svg += `<polygon points="${pts[0].x},${pts[0].y} ${pts[1].x},${pts[1].y} ${pts[2].x},${pts[2].y}" fill="${stroke}"/>`;
        }
      }
    } else if (shape.shape_type === 'rectangle') {
      const x = shape.x - shape.scale_x / 2;
      const y = shape.y - shape.scale_y / 2;
      svg += `<rect x="${x}" y="${y}" width="${shape.scale_x}" height="${shape.scale_y}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="${fill}"/>`;
      
    } else if (shape.shape_type === 'circle') {
      const r = shape.scale_x / 2;
      svg += `<circle cx="${shape.x}" cy="${shape.y}" r="${r}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="${fill}"/>`;
      
    } else if (shape.shape_type === 'ellipse') {
      const rx = shape.scale_x / 2;
      const ry = shape.scale_y / 2;
      svg += `<ellipse cx="${shape.x}" cy="${shape.y}" rx="${rx}" ry="${ry}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="${fill}"/>`;
      
    } else if (shape.shape_type === 'triangle') {
      const w = shape.scale_x;
      const h = shape.scale_y;
      const x1 = shape.x;
      const y1 = shape.y - h / 2;
      const x2 = shape.x - w / 2;
      const y2 = shape.y + h / 2;
      const x3 = shape.x + w / 2;
      const y3 = shape.y + h / 2;
      svg += `<polygon points="${x1},${y1} ${x2},${y2} ${x3},${y3}" stroke="${stroke}" stroke-width="${strokeWidth}" fill="${fill}"/>`;
    } else if (shape.shape_type === 'text') {
      const fs = shape.font_size || 18;
      console.log(shape.font_family)
      svg += `<text x="${shape.x}" y="${shape.y}" fill="${shape.text_color || '#000'}" font-size="${fs}" font-family="${shape.font_family || 'Arial'}">${shape.text}</text>`;
    }
  });
  
  svg += '</svg>';
  return svg;
}
