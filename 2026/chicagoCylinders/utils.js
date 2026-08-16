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
        placeRow.sort();
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
 * Converts a list of bell positions into cylindrical coordinates for a blueline.
 * Handstroke and backstroke are separated and interleaved, so
 * ccwise from the x-axis are 1b, 2h, 3b, 4h, etc. and cwise are 1h, 2b, 3h, 4b, etc.
 * Assumption: starting at backstroke.
 * @param {Array} positions - An array of bell positions, where each position is an integer from 1 to bellCount.
 * @param {number} bellCount - The total number of bells.
 * @returns {Array} An array of three.js vector3 objects representing the line coordinates.
 */
function positions_to_points(positions, bellCount)
{
    const heightStep = Math.PI / bellCount;

    const angles = positions.map((pos, index) => {
        return (pos - 0.5) * [-1, 1][(index + pos) % 2] * (Math.PI / bellCount);
    });

    const points = angles.map((angle, index) => {
        return new THREE.Vector3(Math.cos(angle), -index * heightStep, Math.sin(angle));
    });

    return points;
}