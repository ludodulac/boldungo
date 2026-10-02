export const INITIAL_SOPHIE_PROMPT_V1 = `BOLDÜNGO — ANALYSE V1 INITIALE

Analyse le fichier manifest.json et toutes les photos originales du dossier photos/.

Respecte exactement les photo_id du manifest.

Produis uniquement un ANALYSIS_RESULT valide avec :
schema_version = boldungo.exchange.v1

Utilise exclusivement les familles :
observations
human_facts
entities
relations
uncertainties

et payload.questions pour les questions utiles.

Ne pose une question que si les trois conditions du gate sont réunies :
1. la réponse peut changer matériellement le futur modèle architectural ;
2. les photos actuelles ne suffisent pas ;
3. l'utilisateur peut raisonnablement connaître la réponse sans deviner.

Ne transforme jamais une zone non observable en fait certain.
N'invente aucune information absente des photos.
Ne produis aucune géométrie LEGO.
`;
