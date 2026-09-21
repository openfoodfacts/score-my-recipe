# Changelog

## 1.0.0 (2026-09-21)


### Features

* Account for distances in green score computation ([#55](https://github.com/openfoodfacts/score-my-recipe/issues/55)) ([d2c87e3](https://github.com/openfoodfacts/score-my-recipe/commit/d2c87e39289d8626a0d717862851ae24f0e2db29))
* add dev setup shell script for Linux and macOS ([#11](https://github.com/openfoodfacts/score-my-recipe/issues/11)) ([5dfbf1b](https://github.com/openfoodfacts/score-my-recipe/commit/5dfbf1b3ca31a921fa6f7dcd560e4e14455dd1b7))
* add FastAPI backend with uv setup and dev quick start docs ([8de4f08](https://github.com/openfoodfacts/score-my-recipe/commit/8de4f0806103a105e3ea0df8da60c9a00fe6e19b))
* also match on synonyms ([#27](https://github.com/openfoodfacts/score-my-recipe/issues/27)) ([5bd9d97](https://github.com/openfoodfacts/score-my-recipe/commit/5bd9d974b9e396a8fcdf56ff718cac8f961feb69))
* Compute green score - first iteration ([#28](https://github.com/openfoodfacts/score-my-recipe/issues/28)) ([cfbab94](https://github.com/openfoodfacts/score-my-recipe/commit/cfbab94ec0925b1ef4231f3ee408fe7a93c233b1))
* Create technical-architecture.md ([#49](https://github.com/openfoodfacts/score-my-recipe/issues/49)) ([7bdee3d](https://github.com/openfoodfacts/score-my-recipe/commit/7bdee3de4382bee2574253bf2a451ad65694f8a2))
* EPI score for origins + fix labels edge case ([#50](https://github.com/openfoodfacts/score-my-recipe/issues/50)) ([2efe413](https://github.com/openfoodfacts/score-my-recipe/commit/2efe413d6235a53c596b6dd29b9885ef598c1347))
* first draft home page ([#7](https://github.com/openfoodfacts/score-my-recipe/issues/7)) ([bdb087e](https://github.com/openfoodfacts/score-my-recipe/commit/bdb087e12e1a8d2c9a146c5071a33c68d0ef60fb))
* ingredients list API ([#26](https://github.com/openfoodfacts/score-my-recipe/issues/26)) ([c3c087d](https://github.com/openfoodfacts/score-my-recipe/commit/c3c087db02c8f267cfa21b70020e8f9977cf2a10))
* Ingredients list draft ([#12](https://github.com/openfoodfacts/score-my-recipe/issues/12)) ([ab90310](https://github.com/openfoodfacts/score-my-recipe/commit/ab903101b2f34fb89757a2936fd1ebb87b067216))
* labels list ([#25](https://github.com/openfoodfacts/score-my-recipe/issues/25)) ([51ccdce](https://github.com/openfoodfacts/score-my-recipe/commit/51ccdceed2de46925098adfe575cdc07689346c4))
* origins list ([#22](https://github.com/openfoodfacts/score-my-recipe/issues/22)) ([9e1c345](https://github.com/openfoodfacts/score-my-recipe/commit/9e1c345c8e8b162746324f0aab319ee4e0497e64))
* parse ingredients ([#18](https://github.com/openfoodfacts/score-my-recipe/issues/18)) ([86594f6](https://github.com/openfoodfacts/score-my-recipe/commit/86594f69e2e671bf48926eb0c77e49f9ee5998df))
* signal ingredients that are not scored ([#33](https://github.com/openfoodfacts/score-my-recipe/issues/33)) ([0c37a0d](https://github.com/openfoodfacts/score-my-recipe/commit/0c37a0df5c1f4b1fa8957fd8045a3d1212dc7227))
* suggesting scored ingredients ([#34](https://github.com/openfoodfacts/score-my-recipe/issues/34)) ([1abbcb5](https://github.com/openfoodfacts/score-my-recipe/commit/1abbcb5c4814f64d78cba1ea6c54ce5f7bcb3c29))
* Tags suggestion ([#16](https://github.com/openfoodfacts/score-my-recipe/issues/16)) ([242bcf1](https://github.com/openfoodfacts/score-my-recipe/commit/242bcf127ee63642901a3be62d42236cdb72e5a2))
* taking labels into consideration in green-score computation ([#48](https://github.com/openfoodfacts/score-my-recipe/issues/48)) ([a5462e0](https://github.com/openfoodfacts/score-my-recipe/commit/a5462e0ebd605f1b104ce2f429723a286e44c6ff))


### Bug Fixes

* change wording to make it less catering centric ([#17](https://github.com/openfoodfacts/score-my-recipe/issues/17)) ([1a848d8](https://github.com/openfoodfacts/score-my-recipe/commit/1a848d8ab61c31a175c732a1b482ea1a209262ee))
* minor bug on links ([#15](https://github.com/openfoodfacts/score-my-recipe/issues/15)) ([26a329c](https://github.com/openfoodfacts/score-my-recipe/commit/26a329c3ce8771cee587142a5b35548e665a7aaa))
* replace React landing page with simple Svelte-compatible HTML ([#10](https://github.com/openfoodfacts/score-my-recipe/issues/10)) ([18ae035](https://github.com/openfoodfacts/score-my-recipe/commit/18ae0350f8b9531a1913db28cd20be90ac96ae2e))
* revert bad suggestion ([#20](https://github.com/openfoodfacts/score-my-recipe/issues/20)) ([ddb2d94](https://github.com/openfoodfacts/score-my-recipe/commit/ddb2d946a9abd50a242b3eeda8434df9f3227f08))
* some fix to initial frontend setup ([#5](https://github.com/openfoodfacts/score-my-recipe/issues/5)) ([f1411f6](https://github.com/openfoodfacts/score-my-recipe/commit/f1411f64393bc465fa7525fc6f7de7d071d6677e))
* typo ([170dd4a](https://github.com/openfoodfacts/score-my-recipe/commit/170dd4a1ff4581204e0e999a4503d6330ed1bce0))
* typo in footer ([#13](https://github.com/openfoodfacts/score-my-recipe/issues/13)) ([9bbc794](https://github.com/openfoodfacts/score-my-recipe/commit/9bbc794c3e82a480047c284d93141078ed6b7ec6))
* use interface language to parse recipe ([#38](https://github.com/openfoodfacts/score-my-recipe/issues/38)) ([ad7a170](https://github.com/openfoodfacts/score-my-recipe/commit/ad7a170e3abff57ba12f9e789aa535062a7df39c))
