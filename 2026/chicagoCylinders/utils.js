// Colors match those of https://rsw.me.uk/blueline/methods/
const BLUELINE_COLORS = [
    0xdd1111, 0x1111dd, 0x11dd11, 0xdd11dd, 0xdddd11, 0x11dddd,
    0x306754, 0xaf7817, 0xf75d59, 0x736aff
]

const LINEWIDTH = 7.5; // pixel units

const FRAME_BASE_COLOR = 0x888888;
const FRAME_HIGHLIGHT_COLOR = 0xffffff;
const FRAME_LINEWIDTH = 2; // pixel units

/**
 * Parses a place notation string to complete lists of places made.
 * Symmetry indication with a comma is not yet supported.
 * Letters are converted to numbers, where A=10, B=11, C=12, etc. up to W (x is reserved for cross).
 * See https://ringing.org/methods/ for more information.
 * @param {string} placeNotation - The place notation string to parse.
 * @param {number} bellCount - The total number of bells.
 * @returns {Array} An array of arrays, where each inner array contains the 1-indexed places made at that change.
 */
function parse_place_notation(placeNotation, bellCount)
{
    // Strip whitespace and convert to lowercase
    placeNotation = placeNotation.replaceAll(/\s+/g, '').toLowerCase();

    // Merge duplicate "." into a single "." (multiple . is not standard notation)
    placeNotation = placeNotation.replaceAll(/\.+/g, '.');

    // Ensure each "x" (except one at the start) is preceded by "."
    placeNotation = placeNotation.replaceAll(/(?<=[^\.])x/g, '.x')
    
    // Ensure each "x" (except one at the end) is followed by "."
    placeNotation = placeNotation.replaceAll(/x(?=[^\.])/g, 'x.');

    // Now that they are sandwiched between "."s, we can remove the "x"s
    placeNotation = placeNotation.replaceAll(/x/g, '');

    // Split on "." to get the individual place rows as strings
    const placeRowStrs = placeNotation.split('.');

    // Convert each place row string to an array of integers
    const places = placeRowStrs.map(rowStr => {
        const row = [];
        for (let char of rowStr)
        {
            if (char >= '1' && char <= '9')
            {
                row.push(parseInt(char));
            }
            else if (char >= 'a' && char <= 'w')
            {
                row.push(char.charCodeAt(0) - 'a'.charCodeAt(0) + 10);
            }
            else
            {
                throw new Error(`Invalid character in place notation: ${char}`);
            }
        }
        return row;
    });

    // Insert implied places
    for(let placeRow of places)
    {
        // Check for odd-many changing at row end
        numFreeAtEnd = bellCount - Math.max(...placeRow, 0);
        if (numFreeAtEnd % 2 === 1)
        {
            // Add the last bell to the place row
            placeRow.push(bellCount);
        }

        // Check for odd-many changing at row start
        numFreeAtStart = Math.min(...placeRow, bellCount + 1) - 1;
        if (numFreeAtStart % 2 === 1)
        {
            // Add the first bell to the place row
            placeRow.unshift(1);
        }
    }

    // Ensure no internal places are missing (i.e., the gaps between places should be even-sized)
    for(let placeRow of places)
    {
        placeRow.sort((a, b) => a - b);
        for (let i = 0; i < placeRow.length - 1; i++)
        {
            const gap = placeRow[i + 1] - placeRow[i] - 1; // exclude both endpoints
            if (gap % 2 === 1)
            {
                throw new Error(`Invalid place notation: missing internal places between ${placeRow[i]} and ${placeRow[i + 1]}`);
            }
        }
    }

    return places;
}

/**
 * Converts a list of complete lists of places made at every change.
 * Each row's places need not be sorted, but they are assumed to have even-sized gaps when sorted.
 * Assumption: start in rounds (1, 2, 3, ..., n)
 * @param {Array} places - An array of places made, where each place is an integer from 1 to bellCount.
 * @param {number} bellCount - The total number of bells.
 * @returns {Array} An array of rows, where each row is an array of the 1-indexed bell names.
 */
function places_to_rows(places, bellCount)
{
    const rows = [Array.from({length: bellCount}, (_, i) => i + 1)];
    for (let place_row of places)
    {
        const last_row = rows[rows.length - 1];
        const new_row = Array(bellCount);
        let waiting = null;
        for (let place = 1; place <= bellCount; place++)
        {
            if (place_row.includes(place))
            {
                // Make places
                new_row[place - 1] = last_row[place - 1];
            }
            else if (waiting === null)
            {
                // Wait for the next bell to swap
                waiting = last_row[place - 1];
            }
            else
            {
                // Swap the waiting bell with the current bell
                new_row[place - 2] = last_row[place - 1];
                new_row[place - 1] = waiting;
                waiting = null;
            }
        }
        rows.push(new_row);
    }
    return rows;
}

/**
 * Split a list of rows into a list of positions for each bell.
 * Assumption: start in rounds (1, 2, 3, ..., n)
 * @param {Array} rows - An array of rows, where each row is an array of the 1-indexed bell names.
 * @returns {Array} An array of, for each bell, an array of 1-indexed bell positions.
 */
function rows_to_positions(rows)
{
    const bellCount = rows[0].length;
    const positions = Array.from({length: bellCount}, () => []);

    for (let row of rows)
    {
        for (let i = 0; i < bellCount; i++)
        {
            const bell = row[i];
            positions[bell - 1].push(i + 1);
        }
    }

    return positions;
}

/**
 * Determines the height step between rows given the bell count.
 * @param {number} bellCount - The total number of bells.
 * @returns {number} The height step between rows.
 */
function get_height_step(bellCount)
{
    return Math.PI / bellCount / 2;
}

/**
 * Converts a list of bell positions into cylindrical coordinates for a blueline.
 * Handstroke and backstroke are separated and interleaved, so
 * ccwise from the x-axis are 1b, 2h, 3b, 4h, etc. and cwise are 1h, 2b, 3h, 4b, etc.
 * Assumption: starting at backstroke.
 * @param {Object} HANDLES - Object containing the three.js library and other dependencies.
 * @param {Array} positions - An array of bell positions, where each position is an integer from 1 to bellCount.
 * @param {number} bellCount - The total number of bells.
 * @param {number} scrollParam - The scroll fraction along the method (default is 0, i.e. scrolled to top)
 * @returns {Array} An array of three.js vector3 objects representing the line coordinates.
 */
function positions_to_points(HANDLES, positions, bellCount, scrollParam = 0)
{
    const THREE = HANDLES.THREE;

    const heightStep = get_height_step(bellCount);
    const totalHeight = heightStep * (positions.length - 1);

    const angles = positions.map((pos, index) => {
        return (pos - 0.5) * [-1, 1][(index + pos) % 2] * (Math.PI / bellCount);
    });

    const points = angles.map((angle, index) => {
        return new THREE.Vector3(Math.cos(angle), -index * heightStep + scrollParam * totalHeight, -Math.sin(angle));
        // z-axis is negative to match standard orientation in 2d
    });

    return points;
}

/**
 * Generate a wire frame for the bell lines.
 * @param {Object} HANDLES - Object containing the three.js library and other dependencies.
 * @param {number} bellCount - The total number of bells.
 * @param {number} numRows - The number of rows to generate.
 * @param {number} scrollParam - The scroll fraction along the method (default is 0, i.e. scrolled to top)
 * @param {Function} extractor - A function to extract the position data from each point (default is to extract [x, y, z])
 * @param {number} circle_res_factor - The resolution factor for the circular coordinates (default is 3)
 * @returns {Array} An array of three.js line objects representing the wire frame.
 */
function generate_wire_frame(HANDLES, bellCount, numRows, scrollParam = 0, extractor = (point) => [point.x, point.y, point.z], circle_res_factor = 3)
{
    const THREE = HANDLES.THREE;
    const Line2 = HANDLES.Line2;
    const LineMaterial = HANDLES.LineMaterial;
    const LineGeometry = HANDLES.LineGeometry;

    // Precompute circular coordinates
    const cs_vals = [];
    for (let i = 0; i <= 2 * bellCount * circle_res_factor; i++)
    {
        const angle = (i / circle_res_factor + 0.5) * (Math.PI / bellCount);
        cs_vals.push([Math.cos(angle), Math.sin(angle)]);
    }

    // Precompute height values
    const h_vals = [];
    const heightStep = get_height_step(bellCount);
    const totalHeight = heightStep * (numRows - 1);
    for (let i = 0; i < numRows; i++)
    {
        h_vals.push(-i * heightStep + scrollParam * totalHeight);
    }

    // Create horizontal loops
    const horizontalLines = [];
    for (let i = 0; i < numRows; i++)
    {
        const points = [];
        for (let j = 0; j <= 2 * bellCount * circle_res_factor; j++)
        {
            const [x, z] = cs_vals[j];
            points.push(new THREE.Vector3(x, h_vals[i], -z));
        }
        
        const geometry = new LineGeometry();
        geometry.setPositions(points.flatMap(extractor));
        const material = new LineMaterial({
                color: (i == 0 || i == numRows - 1) ? FRAME_HIGHLIGHT_COLOR : FRAME_BASE_COLOR,
                linewidth: FRAME_LINEWIDTH
            });
        horizontalLines.push(new Line2(geometry, material));
    }

    // Create vertical lines
    const verticalLines = [];
    for (let i = 0; i < 2 * bellCount; i++)
    {
        const points = [];
        for (let j = 0; j < numRows; j++)
        {
            const [x, z] = cs_vals[i * circle_res_factor];
            points.push(new THREE.Vector3(x, h_vals[j], -z));
        }
        
        const geometry = new LineGeometry();
        geometry.setPositions(points.flatMap(extractor));
        const material = new LineMaterial({
                color: (i == 0) ? FRAME_HIGHLIGHT_COLOR : FRAME_BASE_COLOR,
                linewidth: FRAME_LINEWIDTH
            });
        verticalLines.push(new Line2(geometry, material));
    }

    return [...horizontalLines, ...verticalLines];
}

/**
 * Converts a place notation string into a list of three.js line objects.
 * @param {Object} HANDLES - Object containing the three.js library and other dependencies.
 * @param {string} placeNotation - The place notation string to parse.
 * @param {number} bellCount - The total number of bells.
 * @param {number} scrollParam - The scroll fraction along the method (0 = scrolled to top).
 * @param {boolean} includeFrame - Whether to include a wire frame for the lines.
 * @returns {Array} An array of three.js line objects.
 */
function parse_place_notation_to_lines(HANDLES, placeNotation, bellCount, scrollParam, includeFrame, toroid)
{
    const THREE = HANDLES.THREE;
    const Line2 = HANDLES.Line2;
    const LineMaterial = HANDLES.LineMaterial;
    const LineGeometry = HANDLES.LineGeometry;

    // Extract 3d points
    const places = parse_place_notation(placeNotation, bellCount);
    const rows = places_to_rows(places, bellCount);
    const positions = rows_to_positions(rows);
    const points = positions.map(pos => positions_to_points(HANDLES, pos, bellCount, scrollParam));

    // custom extractor to take vectors to lists of points, transforming to toroidal coordinates if requested
    function extractor(point)
    {
        let x = point.x, y = point.y, z = point.z;
        if (toroid)
        {
            const h = get_height_step(bellCount) * (rows.length - 1);
            const R = 1 + Math.max(1, h / (2 * Math.PI));
            const ang = 2 * Math.PI * y / h;
            return [(x - R) * Math.cos(ang) + R, - (x - R) * Math.sin(ang), z];
        }
        return [x, y, z];
    }

    // Create bell lines
    let lines = points.map((bellPoints, index) => {
        const geometry = new LineGeometry();
        geometry.setPositions(bellPoints.flatMap(extractor));
        const material = new LineMaterial({
                color: BLUELINE_COLORS[index % BLUELINE_COLORS.length],
                linewidth: LINEWIDTH // in world units with size attenuation, pixels otherwise
            });
        return new Line2(geometry, material);
    });

    // Optionally add a wire frame
    if (includeFrame)
    {
        lines = [...lines, ...generate_wire_frame(HANDLES, bellCount, rows.length, scrollParam, extractor)];
    }
    /*
    // Optionally convert to torus mode
    if (toroid)
    {
        for (let line of lines)
        {
            for (let i = 0; i < line.geometry.attributes.position.count; i++)
            {
                const x = line.geometry.attributes.position.getX(i);
                const z = line.geometry.attributes.position.getZ(i);
                const angle = Math.atan2(-z, x);
                const radius = Math.sqrt(x * x + z * z);
                line.geometry.attributes.position.setX(i, x + 0.5);// * Math.cos(angle));
                //line.geometry.attributes.position.setZ(i, radius * Math.sin(angle));
                //line.geometry.attributes.position.setY(i, 0);
            }
            line.geometry.computeBoundingSphere();
            line.geometry.computeBoundingBox();
            line.geometry.attributes.position.needsUpdate = true;
        }
    }*/

    return lines;
}