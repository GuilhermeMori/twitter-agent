const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });
const { ApifyClient } = require('apify-client');
const stateManager = require('./utils/state-manager');

const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
});

async function searchTwitter(keywords, minLikes = 0, maxResults = 1000) {
  stateManager.setStep(1, 'Pesquisando tweets no Twitter/X');
  stateManager.setAgentStatus('beto-busca', 'running');

  // Construir query com operadores do Twitter
  let searchQuery = keywords.map(k => `"${k}"`).join(' OR ') + ' lang:pt';
  if (minLikes > 0) {
    searchQuery += ` min_faves:${minLikes}`;
  }

  const input = {
    mode: 'search',
    searchTerms: [searchQuery],
    searchMode: 'Latest',
    maxResults: maxResults,
    twitterCookie: `auth_token=${process.env.TWITTER_AUTH_TOKEN}; ct0=${process.env.TWITTER_CT0}`
  };

  console.log('🔍 Iniciando busca no Twitter via Apify...');
  console.log('Query:', searchQuery);

  try {
    const run = await client.actor('automation-lab/twitter-scraper').call(input);
    const { items } = await client.dataset(run.defaultDatasetId).listItems();

    console.log(`✅ Sucesso! Recebidos ${items.length} tweets da rede.`);

    // Garantir o filtro de likes localmente
    const filteredItems = items
      .filter(tweet => (tweet.likeCount || 0) >= minLikes)
      .map(tweet => ({
        id: tweet.id,
        url: tweet.url,
        author: `@${tweet.authorUsername || 'unknown'}`,
        text: tweet.text,
        likes: tweet.likeCount || 0,
        reposts: tweet.retweetCount || 0,
        replies: tweet.replyCount || 0,
        timestamp: tweet.createdAt
      }));

    console.log(`📊 Após filtragem local (minLikes: ${minLikes}): ${filteredItems.length} tweets qualificados.`);
    stateManager.setAgentStatus('beto-busca', 'idle');
    return filteredItems;
  } catch (error) {
    let errorMsg = error.message;
    if (error.message.includes('APIFY_TOKEN')) {
      errorMsg = 'Token do Apify não configurado ou inválido.';
    }
    console.error('❌ Erro ao buscar tweets:', errorMsg);
    stateManager.setStep(1, 'Erro na Busca', 'error', errorMsg);
    stateManager.setAgentStatus('beto-busca', 'error');
    throw error;
  }
}

// Executar
const fs = require('fs');

async function run() {
  let keywords = ['Brasil jogo', 'Seleção brasileira', 'Endrick Brasil', 'Amistoso seleção', 'Leo Pereira'];
  let minLikes = 0;

  // Tentar ler do arquivo de configuração
  const configPath = path.join(__dirname, '../output/research-focus.md');
  if (fs.existsSync(configPath)) {
    try {
      const content = fs.readFileSync(configPath, 'utf8');
      const kwLines = content.split('## Palavras-chave')[1]?.split('##')[0]?.split('\n') || [];
      const extractedKws = kwLines
        .filter(l => l.trim().startsWith('-'))
        .map(l => l.replace('-', '').trim());

      if (extractedKws.length > 0) keywords = extractedKws;

      const likeMatch = content.match(/Mínimo de Likes: (\d+)/);
      if (likeMatch) minLikes = parseInt(likeMatch[1], 10);

      console.log('📄 Configuração carregada do research-focus.md');
    } catch (e) {
      console.error('⚠️ Falha ao ler research-focus.md');
    }
  }

  try {
    const results = await searchTwitter(keywords, minLikes, 1000);
    const yaml = require('js-yaml');
    const output = yaml.dump({ posts: results });

    // Criar pasta de histórico com timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('.')[0];
    const historyDir = path.join(__dirname, '../output/history', timestamp);

    // Criar diretório se não existir
    if (!fs.existsSync(historyDir)) {
      fs.mkdirSync(historyDir, { recursive: true });
    }

    // Salvar APENAS no histórico (não duplicar na raiz)
    const historyPath = path.join(historyDir, 'raw-posts.md');
    fs.writeFileSync(historyPath, output, 'utf8');
    console.log(`💾 Resultados salvos em: ${historyPath}`);

    // Copiar research-focus.md para o histórico
    if (fs.existsSync(configPath)) {
      const historyConfigPath = path.join(historyDir, 'research-focus.md');
      fs.copyFileSync(configPath, historyConfigPath);
    }

    stateManager.setStep(2, 'Busca concluída', 'success');
    console.log('--- YAML OUTPUT ---');
    console.log('Results length:', results.length);
    console.log('History folder:', timestamp);
  } catch (e) {
    console.error('❌ Erro fatal:', e.message);
    process.exit(1);
  }
}

run();
