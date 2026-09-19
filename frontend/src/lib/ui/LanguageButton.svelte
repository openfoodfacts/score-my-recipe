<script>
	import { _, AVAILABLE_LOCALES } from '$lib/i18n';
	import { locale } from "svelte-i18n";

	function updateLanguage(event) {
		locale.set(event.target.value);
	}
</script>


<div class="locale-selector flex flex-1">
	<div class="select">
		<select value={$locale} onchange={updateLanguage}>
			{#each AVAILABLE_LOCALES as locale }
				<option value={locale.get('code')}>{locale.get('label')}</option>
			{/each}
		</select>
	</div>
</div>


