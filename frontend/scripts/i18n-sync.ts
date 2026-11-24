/**
 * @fileoverview Translation file maintenance: check and sync.
 *
 * Locale files may be **partial**: they only need the keys that were actually
 * translated. A key missing from a locale file is resolved at runtime from the
 * reference locale (`en-US.json`) by svelte-i18n, because `fallbackLocale` is
 * set in `src/lib/i18n/index.ts`.
 * So a missing key is normal and never an error;
 * what must be avoided is a key that no longer exists in the reference (dead key)
 * or a translation whose placeholders do not match the reference.
 *
 * Modes:
 * - `--check` reports extra keys and placeholder mismatches (exit code 1 on error),
 *   and prints the translation coverage of each locale.
 * - `--sync` prunes keys that were removed from the reference,
 *   and drops leaves that are identical to the reference (untranslated leftovers).
 *   It never copies reference values into a target file.
 */
import fs from 'node:fs';
import path from 'node:path';

const MESSAGES_DIR = path.join(process.cwd(), 'src/lib/i18n/messages');

/**
 * A translated leaf, flattened to a dot-notation key.
 * `placeholders` lists the ICU parameters (`{name}`, `{count, number}`…) found in the value.
 */
type Leaf = { value: string; placeholders: string[] };

type FlatMessages = Record<string, Leaf>;

/** Parse command line arguments. */
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
 * Recursively flattens a nested JSON object into dot-notation keys.
 * Example: { navbar: { title: "Hello {name}" } }
 *       -> { "navbar.title": { value: "Hello {name}", placeholders: ["{name}"] } }
 */
function flattenObject(obj: Record<string, unknown>, prefix = ''): FlatMessages {
	const result: FlatMessages = {};

	for (const [key, value] of Object.entries(obj)) {
		const newKey = prefix ? `${prefix}.${key}` : key;

		if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
			Object.assign(result, flattenObject(value as Record<string, unknown>, newKey));
		} else {
			const strValue = String(value);
			result[newKey] = { value: strValue, placeholders: extractPlaceholders(strValue) };
		}
	}

	return result;
}

/** Extracts ICU placeholders from a string (e.g. `{name}` in "Hello {name}"). */
function extractPlaceholders(str: string): string[] {
	return str.match(/\{[^}]+\}/g) || [];
}

/** Recursively expands a flat dot-notation object back into a nested structure. */
function unflattenObject(flat: FlatMessages): Record<string, unknown> {
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

/** Load and flatten one message file. */
function loadFlat(filePath: string): FlatMessages {
	return flattenObject(JSON.parse(fs.readFileSync(filePath, 'utf-8')));
}

/** All locale file names, reference included. */
function listFiles(): string[] {
	return fs.readdirSync(MESSAGES_DIR).filter((f) => f.endsWith('.json'));
}

/**
 * Keys of `target` that do not exist in `reference`.
 * They are dead keys: nothing can request them any more, so they only add noise.
 */
function findExtraKeys(reference: FlatMessages, target: FlatMessages): string[] {
	return Object.keys(target).filter((key) => !(key in reference));
}

/**
 * Translated keys whose placeholders differ from the reference.
 * A mismatch breaks the message formatting at runtime,
 * so it is an error even though the key exists.
 */
function findPlaceholderMismatches(reference: FlatMessages, target: FlatMessages): string[] {
	const mismatches: string[] = [];

	for (const key of Object.keys(target)) {
		if (!(key in reference)) continue;
		const expected = reference[key].placeholders;
		const got = target[key].placeholders;
		if (expected.length !== got.length || !expected.every((p) => got.includes(p))) {
			mismatches.push(`${key}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(got)}`);
		}
	}

	return mismatches;
}

/**
 * Leaves of `target` that carry the reference English text instead of a translation.
 * Those are leftovers copied by the old full-file sync,
 * including near-duplicates that only differ by punctuation or spacing
 * (e.g. "computation(computed)" against "computation (computed)"),
 * so the comparison ignores whitespace and punctuation.
 * They can be removed so that the fallback does the job instead.
 */
function findUntranslatedLeaves(reference: FlatMessages, target: FlatMessages): string[] {
	return Object.keys(target).filter(
		(key) =>
			key in reference &&
			normalizeForComparison(target[key].value) === normalizeForComparison(reference[key].value)
	);
}

/** Lowercase, drop spaces and punctuation, for comparing an English leftover with the reference. */
function normalizeForComparison(value: string): string {
	return value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
}

/** Print up to `limit` items of a list, then an ellipsis summary. */
function printLimited(items: string[], limit = 5) {
	for (const item of items.slice(0, limit)) {
		console.log(`      - ${item}`);
	}
	if (items.length > limit) {
		console.log(`      ... and ${items.length - limit} more`);
	}
}

/** Percentage of reference keys translated in `target`. */
function coverage(reference: FlatMessages, target: FlatMessages): number {
	const refKeys = Object.keys(reference);
	if (refKeys.length === 0) return 100;
	const translated = refKeys.filter((key) => key in target).length;
	return Math.round((translated / refKeys.length) * 100);
}

function check(ref: string) {
	console.log('🔍 Starting i18n check...\n');

	const referencePath = path.join(MESSAGES_DIR, ref);
	if (!fs.existsSync(referencePath)) {
		console.error(`❌ Reference file not found: ${ref}`);
		process.exit(1);
	}

	const referenceFlat = loadFlat(referencePath);
	console.log(`📚 Reference locale: ${ref}`);
	console.log(`   Keys found: ${Object.keys(referenceFlat).length}\n`);

	let errorCount = 0;

	for (const file of listFiles()) {
		if (file === ref) continue;

		const targetFlat = loadFlat(path.join(MESSAGES_DIR, file));
		const extra = findExtraKeys(referenceFlat, targetFlat);
		const mismatches = findPlaceholderMismatches(referenceFlat, targetFlat);

		console.log(`\n📄 Checking: ${file} (${coverage(referenceFlat, targetFlat)}% translated)`);

		if (extra.length === 0 && mismatches.length === 0) {
			console.log(`   ✅ OK! (${Object.keys(targetFlat).length} keys)`);
			continue;
		}

		errorCount += extra.length + mismatches.length;

		if (extra.length > 0) {
			// A dead key is either a leftover or a typo: `pnpm i18nsync` prunes it.
			console.log(`   ⚠️  Keys not in the reference (${extra.length}), run pnpm i18nsync:`);
			printLimited(extra);
		}
		if (mismatches.length > 0) {
			console.log(`   🔤 Placeholder mismatches (${mismatches.length}):`);
			printLimited(mismatches);
		}
	}

	if (errorCount === 0) {
		console.log(`\n✨ Done! All translation files are valid.`);
	} else {
		console.log(`\n⚠️  Done! Found ${errorCount} issue(s).`);
		process.exit(1);
	}
}

function sync(ref: string) {
	console.log('🔄 Starting i18n sync...\n');

	const referencePath = path.join(MESSAGES_DIR, ref);
	if (!fs.existsSync(referencePath)) {
		console.error(`❌ Reference file not found: ${ref}`);
		process.exit(1);
	}

	const referenceFlat = loadFlat(referencePath);
	console.log(`📚 Reference locale: ${ref}`);
	console.log(`   Keys found: ${Object.keys(referenceFlat).length}\n`);

	let syncedCount = 0;

	for (const file of listFiles()) {
		if (file === ref) continue;

		const filePath = path.join(MESSAGES_DIR, file);
		const targetFlat = loadFlat(filePath);
		const extra = new Set(findExtraKeys(referenceFlat, targetFlat));
		const untranslated = new Set(findUntranslatedLeaves(referenceFlat, targetFlat));

		const keptFlat: FlatMessages = {};
		for (const [key, leaf] of Object.entries(targetFlat)) {
			if (extra.has(key) || untranslated.has(key)) continue;
			keptFlat[key] = leaf;
		}

		if (extra.size === 0 && untranslated.size === 0) {
			console.log(`\n📄 ${file}: ✅ already clean (${Object.keys(keptFlat).length} keys)`);
			continue;
		}

		console.log(`\n📄 ${file}`);
		if (extra.size > 0)
			console.log(`   🗑️  Removed ${extra.size} key(s) missing from the reference`);
		if (untranslated.size > 0)
			console.log(`   🗑️  Removed ${untranslated.size} untranslated key(s)`);
		const keptData = unflattenObject(keptFlat);
		fs.writeFileSync(filePath, JSON.stringify(keptData, null, '\t') + '\n', 'utf-8');
		console.log(
			`   ✅ Kept ${Object.keys(keptFlat).length} key(s) (${coverage(referenceFlat, keptFlat)}% translated)`
		);

		syncedCount++;
	}

	console.log(`\n✨ Done! Synced ${syncedCount} translation file(s).`);
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
