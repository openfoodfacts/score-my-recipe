import fs from 'node:fs';
import path from 'node:path';

const MESSAGES_DIR = path.join(process.cwd(), 'src/lib/i18n/messages');

// Parse command line arguments
function parseArgs(): { ref: string; mode: 'sync' | 'check' } {
	const args = process.argv.slice(2);
	let ref = 'en-US.json';
	let mode: 'sync' | 'check' = 'sync';

	for (let i = 0; i < args.length; i++) {
		if (args[i] === '--ref' && args[i + 1]) {
			ref = args[i + 1];
			i++;
		} else if (args[i] === '--check') {
			mode = 'check';
		} else if (args[i] === '--sync') {
			mode = 'sync';
		}
	}

	return { ref, mode };
}

/**
 * Recursively flattens a nested JSON object into a dot-notation key structure.
 * Also extracts placeholder information.
 * Example: { navbar: { title: "Hello {name}" } } -> { "navbar.title": { value: "Hello {name}", placeholders: ["{name}"] } }
 */
function flattenObject(obj: Record<string, unknown>, prefix = ''): Record<string, { value: string; placeholders: string[] }> {
	const result: Record<string, { value: string; placeholders: string[] }> = {};

	for (const [key, value] of Object.entries(obj)) {
		const newKey = prefix ? `${prefix}.${key}` : key;

		if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
			Object.assign(result, flattenObject(value as Record<string, unknown>, newKey));
		} else {
			const strValue = String(value);
			const placeholders = extractPlaceholders(strValue);
			result[newKey] = { value: strValue, placeholders };
		}
	}

	return result;
}

/**
 * Extracts placeholders from a string (e.g., {name}, {count}, etc.)
 */
function extractPlaceholders(str: string): string[] {
	const matches = str.match(/\{[^}]+\}/g) || [];
	return matches;
}

/**
 * Recursively expands a flat dot-notation object back into a nested structure.
 */
function unflattenObject(flat: Record<string, { value: string; placeholders: string[] }>): Record<string, unknown> {
	const result: Record<string, unknown> = {};

	for (const [key, { value }] of Object.entries(flat)) {
		const keys = key.split('.');
		let current: Record<string, unknown> = result;

		for (let i = 0; i < keys.length - 1; i++) {
			const k = keys[i];
			if (!(k in current)) {
				current[k] = {};
			}
			current = current[k] as Record<string, unknown>;
		}

		current[keys[keys.length - 1]] = value;
	}

	return result;
}

/**
 * Synchronizes a target translation file with the reference.
 * - Adds missing keys from reference (with English value)
 * - Removes keys that don't exist in reference
 * - Preserves existing translations for common keys
 */
function syncTranslationFile(
	reference: Record<string, { value: string; placeholders: string[] }>,
	target: Record<string, { value: string; placeholders: string[] }>
): Record<string, { value: string; placeholders: string[] }> {
	const result: Record<string, { value: string; placeholders: string[] }> = {};

	// Add keys from reference (use English value if missing in target)
	for (const [key, refData] of Object.entries(reference)) {
		if (key in target) {
			// Keep existing translation
			result[key] = target[key];
		} else {
			// Add missing key with English translation
			result[key] = refData;
		}
	}

	return result;
}

/**
 * Checks for differences between reference and target files.
 * Returns an object with missing keys, extra keys, and placeholder mismatches.
 */
function checkTranslationFile(
	reference: Record<string, { value: string; placeholders: string[] }>,
	target: Record<string, { value: string; placeholders: string[] }>
): { missing: string[]; extra: string[]; placeholderMismatches: string[] } {
	const missing: string[] = [];
	const extra: string[] = [];
	const placeholderMismatches: string[] = [];

	// Check for missing keys
	for (const key of Object.keys(reference)) {
		if (!(key in target)) {
			missing.push(key);
		}
	}

	// Check for extra keys
	for (const key of Object.keys(target)) {
		if (!(key in reference)) {
			extra.push(key);
		}
	}

	// Check for placeholder mismatches
	for (const key of Object.keys(reference)) {
		if (key in target) {
			const refPlaceholders = reference[key].placeholders;
			const targetPlaceholders = target[key].placeholders;

			if (refPlaceholders.length !== targetPlaceholders.length ||
				!refPlaceholders.every(p => targetPlaceholders.includes(p))) {
				placeholderMismatches.push(
					`${key}: expected ${JSON.stringify(refPlaceholders)}, got ${JSON.stringify(targetPlaceholders)}`
				);
			}
		}
	}

	return { missing, extra, placeholderMismatches };
}

function sync(ref: string) {
	console.log('🔄 Starting i18n sync...\n');

	// Read reference file
	const referencePath = path.join(MESSAGES_DIR, ref);
	if (!fs.existsSync(referencePath)) {
		console.error(`❌ Reference file not found: ${ref}`);
		process.exit(1);
	}

	const referenceContent = fs.readFileSync(referencePath, 'utf-8');
	const referenceData = JSON.parse(referenceContent);
	const referenceFlat = flattenObject(referenceData);

	console.log(`📚 Reference locale: ${ref}`);
	console.log(`   Keys found: ${Object.keys(referenceFlat).length}\n`);

	// Get all JSON files in messages directory
	const files = fs.readdirSync(MESSAGES_DIR).filter((f) => f.endsWith('.json'));

	let syncedCount = 0;

	for (const file of files) {
		// Skip reference file
		if (file === ref) continue;

		const filePath = path.join(MESSAGES_DIR, file);
		const targetContent = fs.readFileSync(filePath, 'utf-8');
		const targetData = JSON.parse(targetContent);
		const targetFlat = flattenObject(targetData);

		console.log(`\n📄 Processing: ${file}`);
		console.log(`   Current keys: ${Object.keys(targetFlat).length}`);

		// Sync translations
		const syncedFlat = syncTranslationFile(referenceFlat, targetFlat);
		const syncedData = unflattenObject(syncedFlat);

		// Write back to file with pretty formatting
		fs.writeFileSync(filePath, JSON.stringify(syncedData, null, 2) + '\n', 'utf-8');

		const addedKeys = Object.keys(referenceFlat).filter((k) => !(k in targetFlat)).length;
		const removedKeys = Object.keys(targetFlat).filter((k) => !(k in referenceFlat)).length;

		console.log(`   ✅ Synced! Added: ${addedKeys}, Removed: ${removedKeys}, Total: ${Object.keys(syncedFlat).length}`);

		syncedCount++;
	}

	console.log(`\n✨ Done! Synced ${syncedCount} translation file(s).`);
}

function check(ref: string) {
	console.log('🔍 Starting i18n check...\n');

	// Read reference file
	const referencePath = path.join(MESSAGES_DIR, ref);
	if (!fs.existsSync(referencePath)) {
		console.error(`❌ Reference file not found: ${ref}`);
		process.exit(1);
	}

	const referenceContent = fs.readFileSync(referencePath, 'utf-8');
	const referenceData = JSON.parse(referenceContent);
	const referenceFlat = flattenObject(referenceData);

	console.log(`📚 Reference locale: ${ref}`);
	console.log(`   Keys found: ${Object.keys(referenceFlat).length}\n`);

	// Get all JSON files in messages directory
	const files = fs.readdirSync(MESSAGES_DIR).filter((f) => f.endsWith('.json'));

	let totalIssues = 0;
	let checkedCount = 0;

	for (const file of files) {
		// Skip reference file
		if (file === ref) continue;

		const filePath = path.join(MESSAGES_DIR, file);
		const targetContent = fs.readFileSync(filePath, 'utf-8');
		const targetData = JSON.parse(targetContent);
		const targetFlat = flattenObject(targetData);

		console.log(`\n📄 Checking: ${file}`);

		const issues = checkTranslationFile(referenceFlat, targetFlat);

		if (issues.missing.length === 0 && issues.extra.length === 0 && issues.placeholderMismatches.length === 0) {
			console.log(`   ✅ OK! (${Object.keys(targetFlat).length} keys)`);
		} else {
			checkedCount++;
			totalIssues += issues.missing.length + issues.extra.length + issues.placeholderMismatches.length;

			if (issues.missing.length > 0) {
				console.log(`   ❌ Missing keys (${issues.missing.length}):`);
				for (const key of issues.missing.slice(0, 5)) {
					console.log(`      - ${key}`);
				}
				if (issues.missing.length > 5) {
					console.log(`      ... and ${issues.missing.length - 5} more`);
				}
			}

			if (issues.extra.length > 0) {
				console.log(`   ⚠️  Extra keys (${issues.extra.length}):`);
				for (const key of issues.extra.slice(0, 5)) {
					console.log(`      - ${key}`);
				}
				if (issues.extra.length > 5) {
					console.log(`      ... and ${issues.extra.length - 5} more`);
				}
			}

			if (issues.placeholderMismatches.length > 0) {
				console.log(`   🔤 Placeholder mismatches (${issues.placeholderMismatches.length}):`);
				for (const mismatch of issues.placeholderMismatches.slice(0, 5)) {
					console.log(`      - ${mismatch}`);
				}
				if (issues.placeholderMismatches.length > 5) {
					console.log(`      ... and ${issues.placeholderMismatches.length - 5} more`);
				}
			}
		}
	}

	if (totalIssues === 0) {
		console.log(`\n✨ Done! All translation files are valid.`);
	} else {
		console.log(`\n⚠️  Done! Found ${totalIssues} issue(s) in ${checkedCount} file(s).`);
		process.exit(1);
	}
}

function main() {
	const { ref, mode } = parseArgs();

	if (mode === 'check') {
		check(ref);
	} else {
		sync(ref);
	}
}

main();
