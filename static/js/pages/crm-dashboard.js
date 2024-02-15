/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./src/es/pages/crm-dashboard.js":
/*!***************************************!*\
  !*** ./src/es/pages/crm-dashboard.js ***!
  \***************************************/
/***/ (() => {

  document.addEventListener('DOMContentLoaded', function() {
    fetch('/gssm/transaction_data')
        .then(response => response.json())
        .then(transactions => {
            const countries = Object.keys(transactions);
            const transactionCounts = Object.values(transactions);

            // Generate the chart
            const options = {
                chart: {
                    type: 'bar'
                },
                series: [{
                    name: 'Transactions',
                    data: transactionCounts
                }],
                xaxis: {
                    categories: countries
                },
                plotOptions: {
                    bar: {
                        horizontal: true
                    }
                },
                dataLabels: {
                    enabled: false
                },
                title: {
                    text: 'Transactions by Country'
                }
            };

            const chart = new ApexCharts(document.querySelector("#transactions-chart"), options);
            chart.render();

            // Generate and display the summary text
            const summaryText = generateSummaryz(transactions);
            document.getElementById('chart-summary').innerHTML = summaryText;
        })
        .catch(error => console.error('Error fetching transaction data:', error));
});

function generateSummaryz(transactions) {
    const totalTransactions = Object.values(transactions).reduce((acc, val) => acc + val, 0);
    const maxTransactions = Math.max(...Object.values(transactions));
    const countryWithMostTransactions = Object.keys(transactions).find(key => transactions[key] === maxTransactions);

    return `A total of <strong>${totalTransactions}</strong> transactions were recorded. ` +
           `The country with the most transactions is <strong>${countryWithMostTransactions}</strong> with <strong>${maxTransactions}</strong> transactions.`;
}





document.addEventListener('DOMContentLoaded', function() {
  fetch('/gssm/transaction_data_en')
      .then(response => response.json())
      .then(transactions => {
          const countries = Object.keys(transactions);
          const transactionCounts = Object.values(transactions);

          // Generate the donut chart
          const options = {
              chart: {
                  type: 'donut'
              },
              title: {
                text: 'Transactions by Entity'
            },
              series: transactionCounts,
              labels: countries,
              responsive: [{
                breakpoint: 480,
                options: {
                  chart: {
                    width: 200
                  },
                  legend: {
                    position: 'bottom'
                  }
                }
              }]
          };

          const chart = new ApexCharts(document.querySelector("#transactions-chart_en"), options);
          chart.render();

          // Generate and display the summary text
          const summaryText = generateSummary(transactions);
          document.getElementById('chart-summary_en').innerHTML = summaryText;
      })
      .catch(error => console.error('Error fetching transaction data:', error));
});

function generateSummary(transactions) {
  const totalTransactions = Object.values(transactions).reduce((acc, val) => acc + val, 0);
  const maxTransactions = Math.max(...Object.values(transactions));
  const entityWithMostTransactions = Object.keys(transactions).find(key => transactions[key] === maxTransactions);

  return `A total of <strong>${totalTransactions}</strong> transactions were recorded. ` +
         `The entity with the most transactions is <strong>${entityWithMostTransactions}</strong> with <strong>${maxTransactions}</strong> transactions.`;
}




document.addEventListener('DOMContentLoaded', function() {
  fetch('/gssm/transaction_data_en')
      .then(response => response.json())
      .then(transactions => {

          // Generate and display the summary text
          const summaryTextTO = generateSummaryTO(transactions);
          document.getElementById('chart-summary_TO').innerHTML = summaryTextTO;

      })
      .catch(error => console.error('Error fetching transaction data:', error));
});


function generateSummaryTO(transactions) {
  const totalTransactionsTO = Object.values(transactions).reduce((acc, val) => acc + val, 0);

  return `${totalTransactionsTO}`;
  
}


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./src/es/pages/crm-dashboard.js"]();
/******/ 	
/******/ })()
;