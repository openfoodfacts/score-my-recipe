<!--
  SpreadsheetImport.svelte

  The "Spreadsheet" tab of the /add page. The user pastes raw clipboard data
  copied from a spreadsheet; the backend detects the separator, header row and
  column roles, then returns the same ingredients as the text parser plus a
  detection report.

  The preview is deliberately read-only: if detection is wrong, the user fixes
  the source table and pastes it again.
-->
<script lang="ts">
	import { _, getLocale } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import {
		apiIngredientsToIngredients,
		parseRecipeCsv,
		type CsvColumnRole,
		type RecipeParseCsvResponse
	} from '$lib/api/recipe';
	import type { Ingredient } from '$lib/types/ingredient';

	let spreadsheetText = $state('');
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let result = $state<RecipeParseCsvResponse | null>(null);
	let controller: AbortController | null = null;

	/** Ingredients converted from the latest successful parse, for the preview. */
	let previewIngredients = $derived<Ingredient[]>(
		result ? apiIngredientsToIngredients(result.ingredients) : []
	);

	/** Map a detected role to its translation key. */
	function roleKey(role: CsvColumnRole | null | undefined): string {
		return role ? `add.spreadsheet.role_${role}` : 'add.spreadsheet.role_unknown';
	}

	/** Format a confidence score as a percentage, or an em dash when absent. */
	function formatConfidence(confidence: number | null | undefined): string {
		return confidence == null ? '—' : `${Math.round(confidence * 100)}%`;
	}

	/** Clear stale results as soon as the pasted text changes. */
	function handleTextChange() {
		result = null;
		error = null;
		if (isLoading) {
			controller?.abort();
			controller = null;
			isLoading = false;
		}
	}

	/** Parse the pasted table through the API. */
	async function handleSubmit(event: Event) {
		event.preventDefault();
		if (!spreadsheetText.trim()) return;

		controller?.abort();
		const currentController = new AbortController();
		controller = currentController;
		isLoading = true;
		error = null;
		result = null;

		try {
			// The recipe is most likely written in the interface language,
			// and the API expects a 2-letter code (eg. "fr").
			const lang = getLocale().split('-')[0];
			const response = await parseRecipeCsv(spreadsheetText, lang, currentController.signal);
			if (controller !== currentController) return;
			result = response;
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			if (controller !== currentController) return;
			error =
				e instanceof Error
					? e.message
					: $_('add.spreadsheet.error_generic', {
							default: 'An unexpected error occurred.'
						});
		} finally {
			if (controller === currentController) {
				controller = null;
				isLoading = false;
			}
		}
	}

	/** Navigate to the score editor with the parsed ingredients. */
	async function handleContinue() {
		if (!result) return;
		// `result` is Svelte reactive state, so its nested objects are proxies.
		// SvelteKit serializes `goto` state with structured clone, which rejects
		// proxies; snapshot it first to get plain objects.
		// https://svelte.dev/docs/svelte/$state#$state.snapshot
		const plainResult = $state.snapshot(result);
		const ingredients = apiIngredientsToIngredients(plainResult.ingredients);
		await goto('/score', { state: { ingredients } });
	}

	// Abort an in-flight parse when the component is destroyed.
	$effect(() => {
		return () => controller?.abort();
	});
</script>

<div class="space-y-6">
	<form onsubmit={handleSubmit} class="space-y-4">
		<div class="form-control w-full space-y-2">
			<label class="label justify-start p-0" for="spreadsheet-text">
				<span class="text-sm font-medium sm:text-base">
					{$_('add.spreadsheet.label', { default: 'Pasted table' })}
				</span>
			</label>
			<p class="text-base-content/70 text-sm">
				{$_('add.spreadsheet.intro', {
					default:
						'Paste a table copied from your spreadsheet. The separator, header row and column roles are detected automatically.'
				})}
			</p>
			<textarea
				id="spreadsheet-text"
				bind:value={spreadsheetText}
				oninput={handleTextChange}
				class="textarea textarea-bordered min-h-64 w-full font-mono text-sm"
				placeholder={$_('add.spreadsheet.placeholder', {
					default:
						'Paste your table here...\n\nExample:\nIngredient\tQuantity\tUnit\tOrigin\tLabels\nApple\t150\tg\tFrance\tOrganic'
				})}
			></textarea>
		</div>

		<button
			type="submit"
			class="btn btn-lg"
			class:btn-primary={!result}
			class:btn-outline={result}
			disabled={isLoading || !spreadsheetText.trim()}
		>
			{#if isLoading}
				<span class="loading loading-spinner"></span>
			{/if}
			{#if isLoading}
				{$_('add.spreadsheet.parsing', { default: 'Parsing...' })}
			{:else}
				{$_('add.spreadsheet.parse_button', { default: 'Parse spreadsheet' })}
			{/if}
		</button>
	</form>

	{#if error}
		<div id="spreadsheet-errors" class="alert alert-error" role="alert">
			<div>
				<h2 class="font-semibold">
					{$_('add.spreadsheet.error_title', { default: 'Could not parse the spreadsheet' })}
				</h2>
				<p>{error}</p>
			</div>
		</div>
	{/if}

	{#if result}
		<section class="space-y-6" aria-labelledby="spreadsheet-detection-title">
			<h2 id="spreadsheet-detection-title" class="text-2xl font-semibold">
				{$_('add.spreadsheet.detection_title', { default: 'Detected table' })}
			</h2>

			<details class="group collapse-arrow bg-base-200 collapse">
				<summary class="collapse-title font-medium">
					<span class="group-open:hidden">
						{$_('add.spreadsheet.details_show', { default: 'See table detection details' })}
					</span>
					<span class="hidden group-open:inline">
						{$_('add.spreadsheet.details_hide', { default: 'Hide table detection details' })}
					</span>
				</summary>
				<div class="collapse-content space-y-6">
					<dl
						id="spreadsheet-detection-details"
						class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4"
					>
						<div>
							<dt class="text-base-content/60">
								{$_('add.spreadsheet.separator', { default: 'Separator' })}
							</dt>
							<dd class="font-medium">
								{#if result.detection.separator === '\t'}
									{$_('add.spreadsheet.separator_tab', { default: 'Tab' })}
								{:else if result.detection.separator === ','}
									{$_('add.spreadsheet.separator_comma', { default: 'Comma' })}
								{:else if result.detection.separator === ';'}
									{$_('add.spreadsheet.separator_semicolon', { default: 'Semicolon' })}
								{:else if result.detection.separator === '|'}
									{$_('add.spreadsheet.separator_pipe', { default: 'Pipe' })}
								{:else}
									{result.detection.separator}
								{/if}
							</dd>
						</div>
						<div>
							<dt class="text-base-content/60">
								{$_('add.spreadsheet.header', { default: 'Header row' })}
							</dt>
							<dd class="font-medium">
								{result.detection.has_header
									? $_('add.yes', { default: 'Yes' })
									: $_('add.no', { default: 'No' })}
							</dd>
						</div>
						<div>
							<dt class="text-base-content/60">
								{$_('add.spreadsheet.row_count', { default: 'Data rows' })}
							</dt>
							<dd class="font-medium">{result.detection.row_count}</dd>
						</div>
						<div>
							<dt class="text-base-content/60">
								{$_('add.spreadsheet.sample_size', { default: 'Rows sampled' })}
							</dt>
							<dd class="font-medium">{result.detection.sample_size}</dd>
						</div>
					</dl>

					<div id="spreadsheetcolumns-detail">
						<h3 class="mb-2 text-lg font-semibold">
							{$_('add.spreadsheet.columns_title', { default: 'Columns' })}
						</h3>
						<div class="overflow-x-auto">
							<table class="table-sm table">
								<thead>
									<tr>
										<th scope="col">
											{$_('add.spreadsheet.column_index', { default: 'Column' })}
										</th>
										<th scope="col">
											{$_('add.spreadsheet.column_header', { default: 'Header' })}
										</th>
										<th scope="col">
											{$_('add.spreadsheet.column_role', { default: 'Detected role' })}
										</th>
										<th scope="col">
											{$_('add.spreadsheet.column_confidence', { default: 'Confidence' })}
										</th>
									</tr>
								</thead>
								<tbody>
									{#each result.detection.columns as column (column.index)}
										<tr>
											<td>{column.index + 1}</td>
											<td>
												{column.header ?? $_('add.spreadsheet.no_value', { default: '—' })}
											</td>
											<td>
												{$_(roleKey(column.role), { default: 'Unassigned' })}
											</td>
											<td>{formatConfidence(column.confidence)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</div>
			</details>

			{#if result.detection.warnings.length > 0}
				<div id="spreadsheet-warnings" class="alert alert-warning" role="status">
					<div>
						<h3 class="font-semibold">
							{$_('add.spreadsheet.warnings_title', { default: 'Warnings' })}
						</h3>
						<ul class="list-disc space-y-1 pl-5">
							{#each result.detection.warnings as warning, index (index)}
								<li>{warning.message ?? warning.id}</li>
							{/each}
						</ul>
					</div>
				</div>
			{/if}

			<div id="spreadsheet-ingredients-preview">
				<h3 class="mb-2 text-lg font-semibold">
					{$_('add.spreadsheet.preview_title', { default: 'Ingredients to score' })}
				</h3>
				<div class="overflow-x-auto">
					<table class="table-sm table">
						<thead>
							<tr>
								<th scope="col">
									{$_('add.spreadsheet.preview_ingredient', { default: 'Ingredient' })}
								</th>
								<th scope="col">
									{$_('add.spreadsheet.preview_quantity', { default: 'Quantity' })}
								</th>
								<th scope="col">
									{$_('add.spreadsheet.preview_unit', { default: 'Unit' })}
								</th>
								<th scope="col">
									{$_('add.spreadsheet.preview_grams', { default: 'Grams' })}
								</th>
								<th scope="col">
									{$_('add.spreadsheet.preview_origin', { default: 'Origin' })}
								</th>
								<th scope="col">
									{$_('add.spreadsheet.preview_labels', { default: 'Labels' })}
								</th>
							</tr>
						</thead>
						<tbody>
							{#each previewIngredients as ingredient (ingredient.id)}
								<tr>
									<td>{ingredient.name}</td>
									<td>
										{ingredient.quantityValue ?? $_('add.spreadsheet.no_value', { default: '—' })}
									</td>
									<td>
										{ingredient.quantityUnit?.label ??
											$_('add.spreadsheet.no_value', { default: '—' })}
									</td>
									<td>
										{ingredient.weight ?? $_('add.spreadsheet.no_value', { default: '—' })}
									</td>
									<td>
										{ingredient.origin?.label ?? $_('add.spreadsheet.no_value', { default: '—' })}
									</td>
									<td>
										{ingredient.labels.length > 0
											? ingredient.labels.map((label) => label.label).join(', ')
											: $_('add.spreadsheet.no_value', { default: '—' })}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>

			<button type="button" class="btn btn-primary btn-lg" onclick={handleContinue}>
				{$_('add.spreadsheet.continue_button', { default: 'Continue to score' })}
			</button>
		</section>
	{/if}
</div>
