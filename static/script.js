// script.js completo e revisado

// Variável global para armazenar os dados
let todasDespesas = [];

function carregarDespesas() {
  fetch('/api/despesas')
    .then(response => response.json())
    .then(despesas => {
      todasDespesas = despesas;
      popularFiltros();
      aplicarFiltros();
    });
}

function popularFiltros() {
  const anos = [...new Set(todasDespesas.map(d => d.data?.split('-')[0]))].filter(Boolean).sort();
  const selectAno = document.getElementById('filtroAno');
  if (selectAno) {
    selectAno.innerHTML = '<option value="">Todos os anos</option>';
    anos.forEach(ano => {
      const option = document.createElement('option');
      option.value = ano;
      option.textContent = ano;
      selectAno.appendChild(option);
    });
  }

  const meses = [...new Set(todasDespesas.map(d => d.data?.split('-')[1]))].filter(Boolean).sort();
  const selectMes = document.getElementById('filtroMes');
  if (selectMes) {
    selectMes.innerHTML = '<option value="">Todos os meses</option>';
    meses.forEach(mes => {
      const option = document.createElement('option');
      option.value = mes;
      option.textContent = mes;
      selectMes.appendChild(option);
    });
  }
}

function aplicarFiltros() {
  const anoSelecionado = document.getElementById('filtroAno')?.value;
  const mesSelecionado = document.getElementById('filtroMes')?.value;
  const categoriaSelecionada = document.getElementById('filtroCategoria')?.value;
  const statusSelecionado = document.getElementById('filtroStatus')?.value;
  const buscaDescricao = document.getElementById('filtroDescricao')?.value?.toLowerCase();

  let despesasFiltradas = todasDespesas;

  if (anoSelecionado) {
    despesasFiltradas = despesasFiltradas.filter(d => d.data.startsWith(anoSelecionado));
  }
  if (mesSelecionado) {
    despesasFiltradas = despesasFiltradas.filter(d => d.data.split('-')[1] === mesSelecionado);
  }
  if (categoriaSelecionada) {
    despesasFiltradas = despesasFiltradas.filter(d => d.categoria === categoriaSelecionada);
  }
  if (statusSelecionado) {
    despesasFiltradas = despesasFiltradas.filter(d => d.status === statusSelecionado);
  }
  if (buscaDescricao) {
    despesasFiltradas = despesasFiltradas.filter(d => d.descricao.toLowerCase().includes(buscaDescricao));
  }

  exibirDespesasAgrupadas(despesasFiltradas);
}

function exibirDespesasAgrupadas(despesas) {
  const container = document.getElementById('resumo');
  if (!container) return;
  container.innerHTML = '';

  const mesesOrdenados = [...new Set(despesas.map(d => d.data.substring(0, 7)))].sort();

  mesesOrdenados.forEach(mes => {
    const despesasDoMes = despesas.filter(d => d.data.startsWith(mes));
    const totalMes = despesasDoMes.reduce((acc, d) => acc + parseFloat(d.valor), 0);

    const divMes = document.createElement('div');
    divMes.classList.add('mes');
    const data = new Date(mes + '-01');
    const nomeMes = data.toLocaleString('default', { month: 'long' });
    divMes.innerHTML = `<h3>${nomeMes.charAt(0).toUpperCase() + nomeMes.slice(1)} ${mes.split('-')[0]} - Total: R$ ${totalMes.toFixed(2)}</h3>`;

    const tabela = document.createElement('table');
    tabela.classList.add('tabela-despesas');
    tabela.innerHTML = `
      <thead><tr>
        <th>Data</th><th>Descrição</th><th>Pagador</th><th>Categoria</th>
        <th>Valor</th><th>Tipo</th><th>Status</th><th>Ações</th>
      </tr></thead>
      <tbody>
        ${despesasDoMes.map(d => `
          <tr>
            <td>${formatarData(d.data)}</td>
            <td>${d.descricao}</td>
            <td>${d.pagador}</td>
            <td>${d.categoria}</td>
            <td>R$ ${parseFloat(d.valor).toFixed(2)}</td>
            <td>${d.tipo}</td>
            <td>${d.status}</td>
            <td>${d.autor ? 'Por: ' + d.autor : ''}</td>
          </tr>`).join('')}
      </tbody>`;

    divMes.appendChild(tabela);
    container.appendChild(divMes);
  });
}

function formatarData(dataISO) {
  const [ano, mes, dia] = dataISO.split('-');
  return `${dia}/${mes}/${ano}`;
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('filtroAno')?.addEventListener('change', aplicarFiltros);
  document.getElementById('filtroMes')?.addEventListener('change', aplicarFiltros);
  document.getElementById('filtroCategoria')?.addEventListener('change', aplicarFiltros);
  document.getElementById('filtroStatus')?.addEventListener('change', aplicarFiltros);
  document.getElementById('filtroDescricao')?.addEventListener('input', aplicarFiltros);

  carregarDespesas();
});
