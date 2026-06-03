user: sagetech
pass_placeholder: le_mot_de_passe_que_tu_choisis

Pour générer le hash SHA-256 :
node -e "console.log(require('crypto').createHash('sha256').update('TON_MOT_DE_PASSE').digest('hex'))"

Puis mets le résultat dans index.html : LOGIN_HASH = 'le_hash...'
