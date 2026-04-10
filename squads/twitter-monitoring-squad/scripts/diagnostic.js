const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });
const { ApifyClient } = require('apify-client');

const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
});

async function diagnosticSearch() {
  const input = {
    mode: 'search',
    searchTerms: ['Brasil'],
    searchMode: 'Top',
    maxResults: 10,
    twitterCookie: `auth_token=${process.env.TWITTER_AUTH_TOKEN}; ct0=${process.env.TWITTER_CT0}`
  };

  console.log('🧪 Iniciando busca de diagnóstico (termo simples: Brasil)...');
  try {
    const run = await client.actor('automation-lab/twitter-scraper').call(input);
    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    console.log(`✅ Resultado: ${items.length} itens encontrados.`);
    if (items.length > 0) {
      console.log('Exemplo de texto:', items[0].text.substring(0, 50));
    }
  } catch (error) {
    console.error('❌ Erro no diagnóstico:', error.message);
  }
}

diagnosticSearch();
