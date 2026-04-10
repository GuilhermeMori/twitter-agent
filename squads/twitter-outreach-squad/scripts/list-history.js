const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const historyDir = path.join(__dirname, '../output/history');

function listHistory() {
  console.log('📚 Histórico de Execuções do Twitter Engagement Squad\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  if (!fs.existsSync(historyDir)) {
    console.log('❌ Nenhum histórico encontrado. Execute o squad primeiro.');
    return;
  }

  const folders = fs.readdirSync(historyDir)
    .filter(f => fs.statSync(path.join(historyDir, f)).isDirectory())
    .sort()
    .reverse(); // Mais recente primeiro

  if (folders.length === 0) {
    console.log('❌ Nenhum histórico encontrado.');
    return;
  }

  folders.forEach((folder, index) => {
    const folderPath = path.join(historyDir, folder);
    const rawPostsPath = path.join(folderPath, 'raw-posts.md');
    const reviewedPath = path.join(folderPath, 'reviewed-comments.md');
    const focusPath = path.join(folderPath, 'research-focus.md');

    console.log(`${index + 1}. ${folder}`);
    console.log(`   📁 Pasta: ${folderPath}`);

    // Ler informações do research-focus
    if (fs.existsSync(focusPath)) {
      try {
        const content = fs.readFileSync(focusPath, 'utf8');
        const kwLines = content.split('## Palavras-chave')[1]?.split('##')[0]?.split('\n') || [];
        const keywords = kwLines
          .filter(l => l.trim().startsWith('-'))
          .map(l => l.replace('-', '').trim());

        if (keywords.length > 0) {
          console.log(`   🔍 Palavras-chave: ${keywords.join(', ')}`);
        }
      } catch (e) {
        // Ignorar erros
      }
    }

    // Ler informações dos posts
    if (fs.existsSync(rawPostsPath)) {
      try {
        const rawData = yaml.load(fs.readFileSync(rawPostsPath, 'utf8'));
        console.log(`   📊 Posts encontrados: ${rawData.posts?.length || 0}`);
      } catch (e) {
        console.log(`   📊 Posts encontrados: N/A`);
      }
    }

    // Ler informações dos comentários
    if (fs.existsSync(reviewedPath)) {
      try {
        const reviewedData = yaml.load(fs.readFileSync(reviewedPath, 'utf8'));
        console.log(`   ✅ Comentários aprovados: ${reviewedData.checks?.length || 0}`);
        console.log(`   ⭐ Score médio: ${reviewedData.summary?.average_score || 'N/A'}/10`);
      } catch (e) {
        console.log(`   ✅ Comentários aprovados: N/A`);
      }
    }

    console.log('');
  });

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  console.log(`Total de execuções: ${folders.length}`);
}

listHistory();
