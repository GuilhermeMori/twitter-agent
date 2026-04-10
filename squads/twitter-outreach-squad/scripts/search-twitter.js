const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });
const { ApifyClient } = require('apify-client');
const stateManager = require('./utils/state-manager');

const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
});

async function searchTwitter(keywords, minLikes = 0, minReplies = 0, hoursBack = 24, profiles = [], maxResults = 1000) {
  // Zeca Garimpo - Discovery Logic
  stateManager.setStep(1, 'Zeca Garimpo: Pesquisando novos tweets');
  stateManager.setAgentStatus('zeca-garimpo', 'running');

  // Construir query com operadores do Twitter
  let searchQuery = '';
  
  if (profiles.length > 0) {
    // Modo Monitoramento de Perfis
    const profileQueries = profiles.map(p => `from:${p.replace('@', '')}`).join(' OR ');
    searchQuery = `(${profileQueries})`;
  } else {
    // Modo Pesquisa por Palavras-chave
    const kwQuery = keywords.map(k => `"${k}"`).join(' OR ');
    searchQuery = `(${kwQuery})`;
  }

  searchQuery += ' lang:en';

  if (minLikes > 0) {
    searchQuery += ` min_faves:${minLikes}`;
  }
  if (minReplies > 0) {
    searchQuery += ` min_replies:${minReplies}`;
  }

  // Adicionar operador de data (since)
  const sinceDate = new Date(Date.now() - hoursBack * 60 * 60 * 1000).toISOString().split('T')[0];
  searchQuery += ` since:${sinceDate}`;

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

    // Garantir o filtro de métricas e tempo localmente
    const cutoff = new Date(Date.now() - hoursBack * 60 * 60 * 1000);
    const filteredItems = items
      .filter(tweet => {
        const isRecent = new Date(tweet.createdAt) >= cutoff;
        const hasLikes = (tweet.likeCount || 0) >= minLikes;
        const hasReplies = (tweet.replyCount || 0) >= minReplies;
        return isRecent && hasLikes && hasReplies;
      })
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

    console.log(`📊 Após filtragem local (minLikes: ${minLikes}, minReplies: ${minReplies}, hoursBack: ${hoursBack}h): ${filteredItems.length} tweets qualificados.`);
    stateManager.setAgentStatus('zeca-garimpo', 'idle');
    return filteredItems;
  } catch (error) {
    let errorMsg = error.message;
    if (error.message.includes('APIFY_TOKEN')) {
      errorMsg = 'Token do Apify não configurado ou inválido.';
    }
    console.error('❌ Erro ao buscar tweets:', errorMsg);
    stateManager.setStep(1, 'Erro na Busca', 'error', errorMsg);
    stateManager.setAgentStatus('zeca-garimpo', 'error');
    throw error;
  }
}

// Executar
const fs = require('fs');

async function run() {
  let keywords = ['DTC brand', 'Meta Ads', 'Performance Marketing'];
  let minLikes = 0;
  let minReplies = 0;
  let hoursBack = 24; // Default 24h
  let profiles = [];

  // Tentar ler do arquivo de configuração
  const configPath = path.join(__dirname, '../config/research-focus.md');
  if (fs.existsSync(configPath)) {
    try {
      const content = fs.readFileSync(configPath, 'utf8');
      const kwLines = content.split('## Keywords')[1]?.split('##')[0]?.split('\n') || [];
      const extractedKws = kwLines
        .filter(l => l.trim().startsWith('-'))
        .map(l => l.replace('-', '').trim());

      if (extractedKws.length > 0) keywords = extractedKws;

      const likeMatch = content.match(/Minimum Likes: (\d+)/);
      if (likeMatch) minLikes = parseInt(likeMatch[1], 10);

      const replyMatch = content.match(/Minimum Replies: (\d+)/);
      if (replyMatch) minReplies = parseInt(replyMatch[1], 10);

      const hoursMatch = content.match(/Last (\d+) hours/);
      const daysMatch = content.match(/Last (\d+) days?/);
      const monthMatch = content.match(/Last (\d+) month/);
      if (hoursMatch) hoursBack = parseInt(hoursMatch[1], 10);
      else if (daysMatch) hoursBack = parseInt(daysMatch[1], 10) * 24;
      else if (monthMatch) hoursBack = parseInt(monthMatch[1], 10) * 30 * 24;

      const profileLines = content.split('## Specific Profiles')[1]?.split('##')[0]?.split('\n') || [];
      const extractedProfiles = profileLines
        .filter(l => l.trim().startsWith('-'))
        .map(l => l.replace('-', '').trim())
        .filter(l => !l.startsWith('(') && !l.includes('Empty') && l !== '');
      
      if (extractedProfiles.length > 0) {
        profiles = extractedProfiles;
        console.log('🎯 Modo Perfil Ativado: Ignorando palavras-chave.');
      }

      console.log('📄 Configuração carregada do research-focus.md:');
      if (profiles.length > 0) {
        console.log(`   - Profiles: ${profiles.join(', ')}`);
      } else {
        console.log(`   - Keywords: ${keywords.join(', ')}`);
      }
      console.log(`   - Minimum Likes: ${minLikes}`);
      console.log(`   - Minimum Replies: ${minReplies}`);
      console.log(`   - Time Interval: Last ${hoursBack} hours`);
    } catch (e) {
      console.error('⚠️ Falha ao ler research-focus.md');
    }
  }

  try {
    const results = await searchTwitter(keywords, minLikes, minReplies, hoursBack, profiles, 1000);
    const yaml = require('js-yaml');
    const output = yaml.dump({ posts: results });

    // Criar pasta de histórico com timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('.')[0];
    const historyDir = path.join(__dirname, '../output/history', timestamp);

    // Criar diretório se não existir
    if (!fs.existsSync(historyDir)) {
      fs.mkdirSync(historyDir, { recursive: true });
    }

    // Salvar no histórico
    const historyPath = path.join(historyDir, 'raw-posts.md');
    fs.writeFileSync(historyPath, output, 'utf8');
    
    // Salvar na raiz para o próximo passo do pipeline
    const rootOutputPath = path.join(__dirname, '../output/raw-posts.md');
    fs.writeFileSync(rootOutputPath, output, 'utf8');
    
    console.log(`💾 Resultados salvos em: ${historyPath}`);
    console.log(`✅ Arquivo root atualizado para o pipeline: ${rootOutputPath}`);

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
