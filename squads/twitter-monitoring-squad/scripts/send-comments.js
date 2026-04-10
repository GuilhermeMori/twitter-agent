const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../../.env') });
const fs = require('fs');
const yaml = require('js-yaml');
const nodemailer = require('nodemailer');
const stateManager = require('./utils/state-manager');
const { getLatestFile, getLatestRunPath } = require('./utils/get-latest-run');

// Função para criar documento Word simples (HTML que o Word pode abrir)
function createWordDocument(checks, rawPostsData) {
  let wordContent = `
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
    <head>
      <meta charset='utf-8'>
      <title>Relatorio Perfil - Comentários Aprovados</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #1DA1F2; }
        .post { margin-bottom: 40px; page-break-inside: avoid; }
        .post-header { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
        .post-text { color: #333; margin: 10px 0; line-height: 1.6; }
        .comment { background: #e8f5fe; padding: 15px; border-left: 4px solid #1DA1F2; margin: 10px 0; white-space: pre-wrap; }
        .scores { font-size: 12px; color: #666; margin-top: 10px; }
        .link { color: #1DA1F2; text-decoration: none; }
      </style>
    </head>
    <body>
      <h1>Relatorio Perfil - Approved Comments</h1>
      <p><strong>Date:</strong> ${new Date().toLocaleDateString('en-US')}</p>
      <p><strong>Total comments:</strong> ${checks.length}</p>
      <hr>
  `;

  checks.forEach((check, index) => {
    const originalPost = rawPostsData.posts.find(p => p.id === check.id);
    wordContent += `
      <div class="post">
        <div class="post-header">
          <h2>Post #${index + 1}</h2>
          <p><strong>Autor:</strong> ${originalPost ? originalPost.author : 'N/A'}</p>
          <p><strong>Link:</strong> <a href="${check.post_url}" class="link">${check.post_url}</a></p>
          <p><strong>Data do Post:</strong> ${originalPost ? new Date(originalPost.timestamp).toLocaleString('en-US') : 'N/A'}</p>
          <p><strong>Engajamento:</strong> ${originalPost ? `${originalPost.likes} likes, ${originalPost.replies} replies, ${originalPost.reposts} reposts` : 'N/A'}</p>
        </div>
        
        <h3>Post Original:</h3>
        <div class="post-text">${originalPost ? originalPost.text : 'Texto não disponível'}</div>
        
        <h3>Comentário Sugerido:</h3>
        <div class="comment">${check.final_output}</div>
        
        <div class="scores">
          <p><strong>Score Médio:</strong> ${check.average_score}/10</p>
          <p><strong>Veredito:</strong> ${check.verdict}</p>
          <p><strong>Notas da Rita:</strong> ${check.notes}</p>
        </div>
      </div>
      <hr>
    `;
  });

  wordContent += `
    </body>
    </html>
  `;

  return wordContent;
}

// Limpa os arquivos de trabalho para o próximo ciclo
function performCleanup() {
  console.log('🧹 Iniciando limpeza pós-envio...');
  const outputDir = path.join(__dirname, '../output');
  const historyDir = path.join(outputDir, 'history');

  // 1. Deletar arquivos raiz em output/
  ['raw-posts.md', 'draft-comments.md', 'reviewed-comments.md'].forEach(file => {
    const filePath = path.join(outputDir, file);
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        console.log(`   - Removido: ${file}`);
      } catch (e) {
        console.error(`   - Erro ao remover ${file}:`, e.message);
      }
    }
  });

  // 2. Limpar histórico (deletar subpastas)
  if (fs.existsSync(historyDir)) {
    const items = fs.readdirSync(historyDir);
    items.forEach(item => {
      const fullPath = path.join(historyDir, item);
      if (fs.statSync(fullPath).isDirectory()) {
        try {
          fs.rmSync(fullPath, { recursive: true, force: true });
          console.log(`   - Histórico removido: ${item}`);
        } catch (e) {
          console.error(`   - Erro ao remover histórico ${item}:`, e.message);
        }
      }
    });
  }
}


async function sendEmail() {
  stateManager.setStep(5, 'Enviando sugestões por E-mail');
  stateManager.setAgentStatus('rita-revisao', 'running');

  // Pegar arquivos da última execução (pasta history)
  const reviewedPath = getLatestFile('reviewed-comments.md');
  const rawPostsPath = getLatestFile('raw-posts.md');
  const latestRunDir = getLatestRunPath();

  if (!reviewedPath || !fs.existsSync(reviewedPath)) {
    const errorMsg = 'Arquivo de comentários revisados não encontrado no histórico.';
    console.error('❌ Erro:', errorMsg);
    stateManager.setStep(5, 'Erro no Envio', 'error', errorMsg);
    return;
  }

  try {
    const reviewedData = yaml.load(fs.readFileSync(reviewedPath, 'utf8'));
    const rawPostsData = yaml.load(fs.readFileSync(rawPostsPath, 'utf8'));

    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.GMAIL_USER,
        pass: process.env.GMAIL_APP_PASSWORD,
      },
    });

    // Separar os 3 primeiros posts para o corpo do e-mail
    const firstThree = reviewedData.checks.slice(0, 3);
    const remaining = reviewedData.checks.slice(3);

    // Construir HTML do e-mail com apenas 3 posts
    let emailHtml = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px;">
        <h2 style="color: #1DA1F2;">🐦 Twitter Engagement Squad - Approval</h2>
        <p>Hello! Today's cycle has been successfully completed.</p>
        <p><strong>Total approved comments:</strong> ${reviewedData.checks.length}</p>
        <p><strong>Average score:</strong> ${reviewedData.summary.average_score}/10</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3>Top 3 Comments:</h3>
    `;

    firstThree.forEach((check, index) => {
      const originalPost = rawPostsData.posts.find(p => p.id === check.id);
      emailHtml += `
        <div style="margin-bottom: 30px; background: #f9f9f9; padding: 15px; border-radius: 8px;">
          <p style="margin: 0 0 5px 0;"><strong>Post #${index + 1}</strong> - ${originalPost ? originalPost.author : 'N/A'}</p>
          <p style="font-size: 13px; margin: 2px 0; color: #666;">Data: ${originalPost ? new Date(originalPost.timestamp).toLocaleDateString('en-US') : 'N/A'}</p>
          <p style="font-size: 13px; margin: 5px 0;"><a href="${check.post_url}" style="color: #1DA1F2; text-decoration: none;">🔗 Ver post no Twitter/X</a></p>
          
          <div style="background: #fff; padding: 10px; margin: 10px 0; border-radius: 5px; font-size: 13px; color: #666;">
            <strong>Post Original:</strong><br>
            ${originalPost ? originalPost.text.substring(0, 150) + (originalPost.text.length > 150 ? '...' : '') : 'N/A'}
          </div>
          
          <div style="background: #e8f5fe; border-left: 4px solid #1DA1F2; padding: 12px; margin-top: 10px;">
            <strong style="color: #1DA1F2;">Comentário Sugerido:</strong>
            <p style="white-space: pre-wrap; margin: 10px 0 0 0; line-height: 1.5;">${check.final_output}</p>
          </div>
          
          <p style="font-size: 11px; color: #666; margin-top: 10px;">
            <strong>Engagement:</strong> ${originalPost ? `${originalPost.likes}L | ${originalPost.replies}R` : 'N/A'} |
            <strong>Score:</strong> ${check.average_score}/10 | 
            <strong>Rita:</strong> ${check.notes}
          </p>
        </div>
      `;
    });

    if (remaining.length > 0) {
      emailHtml += `
        <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-top: 20px;">
          <p style="margin: 0;"><strong>📎 Attachment:</strong> The remaining ${remaining.length} comments are in the attached Word file.</p>
        </div>
      `;
    }

    emailHtml += `
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p><strong>Next steps:</strong></p>
        <ul style="line-height: 1.8;">
          <li>Review the comments above and in the attachment</li>
          <li>Reply to this email with your approval or adjustments</li>
          <li>Or access the dashboard to manage</li>
        </ul>
        <small style="color: #999;">Growth Collective | Strategic Performance Marketing</small>
      </div>
    `;

    // Criar arquivo Word APENAS no histórico
    const wordContent = createWordDocument(reviewedData.checks, rawPostsData);
    const wordPath = path.join(latestRunDir, 'comentarios-aprovados.doc');
    fs.writeFileSync(wordPath, wordContent, 'utf8');

    console.log(`📁 Histórico completo em: ${latestRunDir}`);

    const mailOptions = {
      from: process.env.GMAIL_USER,
      to: process.env.GMAIL_USER,
      subject: `🚀 Relatorio Perfil: ${reviewedData.checks.length} Approved Comments`,
      html: emailHtml,
      attachments: [
        {
          filename: `Twitter_Comments_${new Date().toISOString().split('T')[0]}.doc`,
          path: wordPath
        }
      ]
    };

    console.log('📬 Enviando e-mail para:', mailOptions.to);
    console.log(`📎 Anexando arquivo Word com ${reviewedData.checks.length} comentários`);
    const info = await transporter.sendMail(mailOptions);
    console.log('✅ E-mail enviado com sucesso! MessageID:', info.messageId);

    // Limpeza automática para garantir um novo ciclo limpo
    performCleanup();

    // Finalizar estado
    stateManager.setStep(5, 'Aprovação do Usuário', 'waiting_approval');
    stateManager.setAgentStatus('rita-revisao', 'idle');

  } catch (error) {
    console.error('❌ Erro no processo de envio:', error);
    stateManager.setStep(5, 'Erro no Envio', 'error', error.message);
    stateManager.setAgentStatus('rita-revisao', 'error');
  }
}

sendEmail();
