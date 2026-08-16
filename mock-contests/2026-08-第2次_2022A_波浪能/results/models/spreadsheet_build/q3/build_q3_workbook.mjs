import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const contestDir = path.resolve(scriptDir, "..", "..", "..", "..");
const templatePath = path.join(
  contestDir,
  "data",
  "raw",
  "result3_官方空白模板.xlsx",
);
const dataPath = path.join(
  contestDir,
  "results",
  "models",
  "q3_full_response.json",
);
const outputPath = path.join(contestDir, "results", "tables", "result3.xlsx");
const previewDir = path.join(scriptDir, "previews");

const stateOrder = [
  "float_heave_displacement",
  "float_heave_velocity",
  "oscillator_heave_displacement",
  "oscillator_heave_velocity",
  "float_pitch_displacement",
  "float_pitch_velocity",
  "oscillator_pitch_displacement",
  "oscillator_pitch_velocity",
];


async function importWorkbook(inputPath) {
  const input = await FileBlob.load(inputPath);
  return SpreadsheetFile.importXlsx(input);
}


async function renderRange(workbook, filename, range) {
  const preview = await workbook.render({
    sheetName: "Sheet1",
    range,
    scale: 1.5,
    format: "png",
  });
  await fs.mkdir(previewDir, { recursive: true });
  await fs.writeFile(
    path.join(previewDir, filename),
    new Uint8Array(await preview.arrayBuffer()),
  );
}


function assertData(payload) {
  if (payload.status !== "frozen_after_full_validation") {
    throw new Error("数据尚未处于完整验证后的固化状态");
  }
  if (JSON.stringify(payload.state_order) !== JSON.stringify(stateOrder)) {
    throw new Error("固化数据状态顺序与 result3 模板不一致");
  }
  if (!Array.isArray(payload.time) || payload.time.length !== 733) {
    throw new Error("时间序列必须包含 733 项");
  }
  if (!Array.isArray(payload.states) || payload.states.length !== 733) {
    throw new Error("状态数据必须包含 733 行");
  }
  if (
    payload.states.some(
      (row) =>
        !Array.isArray(row)
        || row.length !== 8
        || row.some((value) => !Number.isFinite(value)),
    )
  ) {
    throw new Error("每行必须包含八个有限状态值");
  }
}


function workbookRows(payload) {
  return payload.time.map((time, index) => {
    const state = payload.states[index];
    return [
      time,
      state[0],
      state[1],
      state[4],
      state[5],
      state[2],
      state[3],
      state[6],
      state[7],
    ];
  });
}


async function inspectTemplate() {
  const workbook = await importWorkbook(templatePath);
  const overview = await workbook.inspect({
    kind: "workbook,sheet,region,computedStyle",
    sheetId: "Sheet1",
    range: "A1:I12",
    maxChars: 12000,
    tableMaxRows: 12,
    tableMaxCols: 9,
  });
  console.log(overview.ndjson);
  await renderRange(workbook, "template.png", "A1:I12");
}


function extendTemplateFormatting(sheet) {
  let destinationRow = 13;
  while (destinationRow <= 735) {
    const rows = Math.min(10, 736 - destinationRow);
    const sourceEnd = 2 + rows;
    const destinationEnd = destinationRow + rows - 1;
    sheet
      .getRange(`A${destinationRow}:I${destinationEnd}`)
      .copyFrom(sheet.getRange(`A3:I${sourceEnd}`), "all");
    destinationRow += rows;
  }
}


async function buildWorkbook() {
  const payload = JSON.parse(await fs.readFile(dataPath, "utf8"));
  assertData(payload);
  const workbook = await importWorkbook(templatePath);
  const sheet = workbook.worksheets.getItem("Sheet1");
  extendTemplateFormatting(sheet);
  const rows = workbookRows(payload);
  const dataRange = sheet.getRange("A3:I735");
  dataRange.values = rows;
  dataRange.format.horizontalAlignment = "center";
  dataRange.format.verticalAlignment = "center";
  dataRange.format.font = { name: "Times New Roman", size: 11 };
  dataRange.format.borders = {
    preset: "all",
    style: "thin",
    color: "#000000",
  };
  dataRange.format.rowHeight = 14;
  sheet.getRange("A3:A735").format.numberFormat = "0.0";
  sheet.getRange("B3:I735").format.numberFormat = "0.000000";

  const top = await workbook.inspect({
    kind: "region",
    sheetId: "Sheet1",
    range: "A1:I8",
    maxChars: 5000,
    tableMaxRows: 8,
    tableMaxCols: 9,
  });
  const key = await workbook.inspect({
    kind: "region",
    sheetId: "Sheet1",
    range: "A51:I55",
    maxChars: 4000,
    tableMaxRows: 5,
    tableMaxCols: 9,
  });
  const tail = await workbook.inspect({
    kind: "region",
    sheetId: "Sheet1",
    range: "A731:I735",
    maxChars: 4000,
    tableMaxRows: 5,
    tableMaxCols: 9,
  });
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "result3 formula error scan before export",
  });
  console.log("--- top ---");
  console.log(top.ndjson);
  console.log("--- 10 s key region ---");
  console.log(key.ndjson);
  console.log("--- tail ---");
  console.log(tail.ndjson);
  console.log("--- errors ---");
  console.log(errors.ndjson);

  await renderRange(workbook, "filled_top.png", "A1:I16");
  await renderRange(workbook, "filled_key_10s.png", "A49:I56");
  await renderRange(workbook, "filled_tail.png", "A728:I735");
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  console.log(JSON.stringify({ output: outputPath, rows: 733, columns: 9 }));
}


async function verifyWorkbook() {
  const payload = JSON.parse(await fs.readFile(dataPath, "utf8"));
  assertData(payload);
  const expected = workbookRows(payload);
  const workbook = await importWorkbook(outputPath);
  const sheet = workbook.worksheets.getItem("Sheet1");
  const actual = sheet.getRange("A3:I735").values;
  if (actual.length !== 733 || actual.some((row) => row.length !== 9)) {
    throw new Error("导出工作簿数据区形状不是 733×9");
  }

  let maximumDifference = 0;
  let mismatchCount = 0;
  for (let row = 0; row < 733; row += 1) {
    for (let column = 0; column < 9; column += 1) {
      const difference = Math.abs(Number(actual[row][column]) - expected[row][column]);
      maximumDifference = Math.max(maximumDifference, difference);
      if (!Number.isFinite(difference) || difference > 1e-12) {
        mismatchCount += 1;
      }
    }
  }
  if (mismatchCount !== 0) {
    throw new Error(`全部数据区发现 ${mismatchCount} 个不一致单元格`);
  }

  const keyRows = [3, 53, 103, 203, 303, 503, 735];
  const keyValues = {};
  for (const excelRow of keyRows) {
    keyValues[String(excelRow)] = sheet.getRange(`A${excelRow}:I${excelRow}`).values[0];
  }
  const used = await workbook.inspect({
    kind: "region",
    sheetId: "Sheet1",
    range: "A1:I735",
    maxChars: 1500,
    tableMaxRows: 4,
    tableMaxCols: 9,
  });
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "result3 exported formula error scan",
  });
  console.log(used.ndjson);
  console.log(errors.ndjson);
  console.log(
    JSON.stringify(
      {
        data_rows: actual.length,
        data_columns: actual[0].length,
        numeric_cells_checked: 733 * 9,
        mismatch_count: mismatchCount,
        maximum_absolute_difference: maximumDifference,
        key_rows: keyValues,
      },
      null,
      2,
    ),
  );

  await renderRange(workbook, "exported_top.png", "A1:I16");
  await renderRange(workbook, "exported_key_10s.png", "A49:I56");
  await renderRange(workbook, "exported_tail.png", "A728:I735");
  await renderRange(workbook, "exported_tail_float.png", "A728:E735");
  await renderRange(workbook, "exported_tail_oscillator.png", "F728:I735");
}


const mode = process.argv[2] ?? "inspect";
if (mode === "inspect") {
  await inspectTemplate();
} else if (mode === "build") {
  await buildWorkbook();
} else if (mode === "verify") {
  await verifyWorkbook();
} else {
  throw new Error(`未知模式: ${mode}`);
}
