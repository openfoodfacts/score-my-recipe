<!--
  Recipe metadata fields shared by the add (`/add`) and edit (`/score`) views.

  The title and description are optional. On the edit view the title input is
  rendered with heading-like typography because it replaces the former static
  page header; the description stays a compact two-row textarea everywhere.
-->
<script lang="ts">
	import { _ } from '$lib/i18n';

	type Props = {
		/** Recipe title, bound to the caller's state. */
		title?: string;
		/** Recipe description, bound to the caller's state. */
		description?: string;
		/** prefix for ids **/
		idPrefix?: string;
		/** Use heading-like typography for the title input (edit view). */
		headingTitle?: boolean;
	};

	let {
		title = $bindable(''),
		description = $bindable(''),
		idPrefix = '',
		headingTitle = false
	}: Props = $props();
</script>

<div class="space-y-4">
	<div class="form-control w-full space-y-2">
		<label class="label justify-start p-0" for="{idPrefix}recipe-title">
			<span class="text-sm font-medium sm:text-base">
				{$_('recipe.title_label', { default: 'Recipe title' })}
			</span>
		</label>
		<input
			id="{idPrefix}recipe-title"
			type="text"
			class="input input-bordered w-full {headingTitle ? 'h-auto py-2 text-3xl font-bold' : ''}"
			placeholder={$_('recipe.title_placeholder', { default: 'e.g. Quiche Lorraine' })}
			maxlength={120}
			bind:value={title}
		/>
	</div>

	<div class="form-control w-full space-y-2">
		<label class="label justify-start p-0" for="{idPrefix}recipe-description">
			<span class="text-sm font-medium sm:text-base">
				{$_('recipe.description_label', { default: 'Description' })}
			</span>
		</label>
		<textarea
			id="{idPrefix}recipe-description"
			class="textarea textarea-bordered min-h-0 w-full resize-none text-sm leading-snug"
			rows={2}
			maxlength={500}
			placeholder={$_('recipe.description_placeholder', { default: 'Optional short description' })}
			bind:value={description}
		></textarea>
	</div>
</div>
