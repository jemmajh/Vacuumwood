/**
 * Code.gs
 *
 * Binds HTML form to your Spreadsheet’s named ranges and returns both
 * the key numeric outputs (year 1 sales, costs, margin, payback) as well
 * as the 10‐year forecast for Discounted Sales, Cumulative, and Net.
 */

function doGet() {
  const ss = SpreadsheetApp.getActive();
  const template = HtmlService.createTemplateFromFile('index');

  // Prefill template variables by reading each input named range:
  template.input_length        = ss.getRangeByName('input_length').getValue();
  template.input_width         = ss.getRangeByName('input_width').getValue();
  template.input_height        = ss.getRangeByName('input_height').getValue();
  template.input_floorEff      = ss.getRangeByName('input_floorEff').getValue();
  template.input_floors        = ss.getRangeByName('input_floors').getValue();
  template.input_lettuceShare  = ss.getRangeByName('input_lettuceShare').getValue();
  template.input_yield_lettuce = ss.getRangeByName('input_yield_lettuce').getValue();
  template.input_price_lettuce = ss.getRangeByName('input_price_lettuce').getValue();
  template.input_yield_basil   = ss.getRangeByName('input_yield_basil').getValue();
  template.input_price_basil   = ss.getRangeByName('input_price_basil').getValue();
  template.input_buildingCost  = ss.getRangeByName('input_buildingCost').getValue();
  template.input_equipmentCost = ss.getRangeByName('input_equipmentCost').getValue();
  template.input_otherCost     = ss.getRangeByName('input_otherCost').getValue();
  template.input_subsidies     = ss.getRangeByName('input_subsidies').getValue();
  template.input_discountRate  = ss.getRangeByName('input_discountRate').getValue();
  template.input_year1Eff      = ss.getRangeByName('input_year1Eff').getValue();
  template.input_effGain       = ss.getRangeByName('input_effGain').getValue();
  template.input_years         = ss.getRangeByName('input_years').getValue();
  template.input_cost_electricity = ss.getRangeByName('input_cost_electricity').getValue();
  template.input_cost_labor       = ss.getRangeByName('input_cost_labor').getValue();
  template.input_cost_other_ops   = ss.getRangeByName('input_cost_other_ops').getValue();
  template.input_cost_logistics   = ss.getRangeByName('input_cost_logistics').getValue();
  template.input_cost_maintenance = ss.getRangeByName('input_cost_maintenance').getValue();

  // Serve the HTML with those template values injected:
  return template.evaluate().setTitle('Vertical Farming Model');
}


/**
 * Called from index.html when the user clicks “Recalculate”.
 *
 * @param {Object} params  – JS object containing all new input values from the form.
 * @return {Object}        – JS object returning:
 *                           • totalSales, totalCosts, yearlyMargin, paybackYear
 *                           • forecast: an array of { year, discSales, cumSales, net } for years 0–10.
 */
function updateFromWeb(params) {
  const ss = SpreadsheetApp.getActive();

  // 1) Write each input back into its named range:
  ss.getRangeByName('input_length').setValue(params.length);
  ss.getRangeByName('input_width').setValue(params.width);
  ss.getRangeByName('input_height').setValue(params.height);
  ss.getRangeByName('input_floorEff').setValue(params.floorEff);
  ss.getRangeByName('input_floors').setValue(params.floors);
  ss.getRangeByName('input_lettuceShare').setValue(params.lettuceShare);
  ss.getRangeByName('input_yield_lettuce').setValue(params.yieldLettuce);
  ss.getRangeByName('input_price_lettuce').setValue(params.priceLettuce);
  ss.getRangeByName('input_yield_basil').setValue(params.yieldBasil);
  ss.getRangeByName('input_price_basil').setValue(params.priceBasil);
  ss.getRangeByName('input_buildingCost').setValue(params.buildingCost);
  ss.getRangeByName('input_equipmentCost').setValue(params.equipmentCost);
  ss.getRangeByName('input_otherCost').setValue(params.otherCost);
  ss.getRangeByName('input_subsidies').setValue(params.subsidies);
  ss.getRangeByName('input_discountRate').setValue(params.discountRate);
  ss.getRangeByName('input_year1Eff').setValue(params.year1Eff);
  ss.getRangeByName('input_effGain').setValue(params.effGain);
  ss.getRangeByName('input_years').setValue(params.years);
  ss.getRangeByName('input_cost_electricity').setValue(params.electricityCost);
  ss.getRangeByName('input_cost_labor').setValue(params.laborCost);
  ss.getRangeByName('input_cost_other_ops').setValue(params.otherOpsCost);
  ss.getRangeByName('input_cost_logistics').setValue(params.logisticsCost);
  ss.getRangeByName('input_cost_maintenance').setValue(params.maintenanceCost);


  // Force the sheet to recalc (so the Payback sheet updates its 10‐year table)
  SpreadsheetApp.flush();

  // 2) Read back the key numeric outputs via named ranges:
  const totalSales   = ss.getRangeByName('output_yearlySales').getValue();
  const totalCosts   = ss.getRangeByName('output_yearlyCosts').getValue();
  const yearlyMargin = ss.getRangeByName('output_yearlyMargin').getValue();
  const paybackYear  = ss.getRangeByName('output_paybackYear').getValue();

  // 3) Read the full 10‐year forecast table from the “Takaisinmaksu” sheet:
  const paybackSheet = ss.getSheetByName('Takaisinmaksu');
  // Rows 16 through 16+params.years (e.g. if params.years = 10, rows 16–26)
  const lastRow      = 16 + params.years;
  // We know columns: A=Year, B=Discounted Sales, C=Cumulative, D=(skip), E=Net
  const rawRange     = paybackSheet.getRange(`A16:E${lastRow}`);
  const rawValues    = rawRange.getValues(); // 2D array [[year, disc, cum, x, net], …]

  // Map into an array of JSON‐friendly objects:
  const forecast = rawValues.map(row => ({
    year:       row[0],
    discSales:  row[1],
    cumSales:   row[2],
    net:        row[4]
  }));

  // 4) Return everything to the client in one object:
  return {
    totalSales:    totalSales,
    totalCosts:    totalCosts,
    yearlyMargin:  yearlyMargin,
    paybackYear:   paybackYear,
    forecast:      forecast
  };
}


/**
 * Optional helper to include other partial HTML files.
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}
