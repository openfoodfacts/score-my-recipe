# Score a recipe through the API

This tutorial computes a Green-Score from a weighed ingredient and shows how to use the API from another application.
Start the local backend using the [Developer Quick Start](dev-quick-start.md).
Run the commands in the same shell with curl 7.82 or newer and jq.

## 1. Look up the ingredient

Use the ingredient catalog to find a taxonomy ID that the scoring API recognizes.
This command finds the entry for apple.

```sh
api=http://localhost:8000

curl --fail-with-body --silent --show-error "$api/v1/ingredients?lang=en" |
  jq '.ingredients[] | select(.id == "en:apple") | {id, label}'
```

Use the ID in the score request.
The displayed label can change with the language, while the ID stays the same.

## 2. Send the recipe for scoring

Post a JSON object with an `ingredients` array to `/v1/green-score`.
Give each ingredient its own `id` so you can match the response's ingredient notes to your rows.
Use grams for `weight`.
The optional `country` is where the recipe is consumed and is used in the distance calculation.
An ingredient's origin, if known, is a separate field.

```sh
curl --fail-with-body --silent --show-error --json @- "$api/v1/green-score" <<'JSON'
{
  "country": "FR",
  "ingredients": [
    {
      "id": "apple-1",
      "name": "Apple",
      "weight": 150,
      "codifiedIngredient": {
        "id": "en:apple",
        "label": "Apple",
        "isInTaxonomy": true
      }
    }
  ]
}
JSON
```

## 3. Read the result

The result includes `numericScore` and `letterGrade`.
A successful response can contain `missingIngredientIds` if there is no Agribalyse match for some ingredients.
Check that list before displaying the score as covering the whole recipe.
If nothing could be scored, the score and grade are both `null`.
Read `notes` for recipe-level explanations and `ingredientsNotes` for notes keyed by the IDs you sent.
The optional request field `lang` selects the language of the notes.

## Start with recipe text

If your application starts from free text, call `POST /v1/parse_text` to get ingredient suggestions.

```sh
curl --fail-with-body --silent --show-error --json @- "$api/v1/parse_text" <<'JSON'
{
  "lang": "fr",
  "text": "1 pâte brisée (150g)\n4 pommes bio\n50g de sucre\n30g de beurre origine France"
}
JSON
```

Review the returned ingredients before scoring, especially entries with no taxonomy match or no quantity in grams.
For an ingredient you confirmed, use `taxonomy_id` as `codifiedIngredient.id`, `codified_ingredient` as its label, and `is_in_taxonomy` as `isInTaxonomy`.
Use the confirmed `quantity_g` as `weight`.
Add your own unique row ID and display name, then send the score request shown above with the complete ingredient list.

See the [OpenAPI reference](openapi.json) or the local Swagger UI at <http://localhost:8000/docs> for the full schemas and other endpoints.
