// script.js

function carregarDespesas() {
  fetch('/api/despesas')
    .then(response => response.json())
    .then(despesas => {
      const container = document.getElementById('resumo');
      container.innerHTML = '';

      // Extrair anos válidos das datas
      const anos = [...new Set(despesas.map(d => d.data?.split('-')[0]).filter(Boolean))]
        .map(Number)
        .filter(ano => !isNaN(ano))
        .sort();

      anos.forEach(ano => {
        const despesasDoAno = despesas.filter(d => d.data.startsWith(ano.toString()));
        const totalAno = despesasDoAno.reduce((soma, d) => soma + parseFloat(d.valor), 0);

        const divAno = document.createElement('div');
        divAno.classList.add('ano');
        divAno.innerHTML = `<h2>${ano}</h2><p>Total: R$ ${totalAno.toFixed(2)}</p>`;

        despesasDoAno.forEach(despesa => {
          const div = document.createElement('div');
          div.classList.add('despesa');
          div.innerHTML = `
            <strong>${despesa.data}</strong>: ${despesa.descricao} - R$ ${parseFloat(despesa.valor).toFixed(2)} <em>(${despesa.pagador})</em>
          `;
          divAno.appendChild(div);
        });

        container.appendChild(divAno);
      });
    });
}

document.addEventListener('DOMContentLoaded', carregarDespesas);
