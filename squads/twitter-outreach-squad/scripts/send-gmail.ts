// @ts-nocheck
import nodemailer from 'nodemailer';

/**
 * Script para enviar notificação de aprovação via Gmail SMTP.
 * Requer as seguintes variáveis de ambiente no .env:
 * - GMAIL_USER: Seu e-mail do Gmail.
 * - GMAIL_APP_PASSWORD: Senha de app gerada na conta Google.
 */

async function sendApprovalEmail(to, postUrl, originalText, suggestedComment) {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.GMAIL_USER,
      pass: process.env.GMAIL_APP_PASSWORD,
    },
  });

  const mailOptions = {
    from: process.env.GMAIL_USER,
    to: to,
    subject: '🚨 Aprovação de Squad: Novo Comentário Twitter/X',
    html: `
      <h2>Nova Sugestão de Engajamento</h2>
      <p>O <b>Twitter Engagement Squad</b> localizou um post relevante e gerou uma proposta:</p>
      
      <hr>
      <h3>📌 Post Original:</h3>
      <p><a href="${postUrl}">Ver no Twitter/X</a></p>
      <blockquote>${originalText}</blockquote>
      
      <hr>
      <h3>✍️ Comentário Sugerido (Cadu Comentário):</h3>
      <div style="background-color: #f4f4f4; padding: 15px; border-radius: 8px;">
        ${suggestedComment.replace(/\n/g, '<br>')}
      </div>
      
      <hr>
      <p>Favor responder no chat do terminal com <b>"Sim"</b> para postar ou <b>"Não + Motivo"</b> para o Cadu refazer.</p>
    `,
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('Email enviado: ' + info.response);
    return true;
  } catch (error) {
    console.error('Erro ao enviar e-mail:', error);
    return false;
  }
}

// Execução se chamado diretamente
if (process.argv[2]) {
  const data = JSON.parse(process.argv[2]);
  sendApprovalEmail(data.to, data.postUrl, data.originalText, data.suggestedComment);
}
