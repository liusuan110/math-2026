import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const contestDir = path.resolve(scriptDir, "..", "..", "..");
const rawDir = path.join(contestDir, "data", "raw");
const outputDir = path.join(contestDir, "results", "tables");
const previewDir = path.join(scriptDir, "previews");
const dataPath = path.join(scriptDir, "..", "q1_full_response.json");

const workbooks = [
  {
    key: "constant",
    input: path.join(rawDir, "result1-1_官方空白模板.xlsx"),
    output: path.join(outputDir, "result1-1.xlsx"),
  },
  {
    key: "power",
    input: path.join(rawDir, "result1-2_官方空白模板.xlsx"),
    output: path.join(outputDir, "result1-2.xlsx"),
  },
];


async function importWorkbook(inputPath) {
  const input = await FileBlob.load(inputPath);
  return SpreadsheetFile.importXlsx(input);
}


async function renderWorkbook(workbook, outputPath, range = "A1:E12") {
  const preview = await workbook.render({
    sheetName: "Sheet1",
    range,
    scale: 1.5,
    format: "png",
  });
  await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
}


async function previewTemplates() {
  await fs.mkdir(previewDir, { recursive: true });
  for (const spec of workbooks) {
    const workbook = await importWorkbook(spec.input);
    const overview = await workbook.inspect({
      kind: "workbook,sheet,region,computedStyle",
      sheetId: "Sheet1",
      range: "A1:E12",
      maxChars: 8000,
      tableMaxRows: 12,
      tableMaxCols: 5,
    });
    console.log(`--- ${spec.key} template ---`);
    console.log(overview.ndjson);
    await renderWorkbook(
      workbook,
      path.join(previewDir, `${spec.key}_template.png`),
    );
  }
}


function assertResponseData(data) {
  if (!Array.isArray(data.time) || data.time.length !== 898) {
    throw new Error("时间序列必须包含 898 项");
  }
  for (const key of ["constant", "power"]) {
    if (!Array.isArray(data[key]) || data[key].length !== 4) {
      throw new Error(`${key} 必须包含四个状态序列`);
    }
    if (data[key].some((series) => !Array.isArray(series) || series.length !== 898)) {
      throw new Error(`${key} 的每个状态序列必须包含 898 项`);
    }
  }
}


async function buildWorkbooks() {
  const data = JSON.parse(await fs.readFile(dataPath, "utf8"));
  assertResponseData(data);
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });

  for (const spec of workbooks) {
    const workbook = await importWorkbook(spec.input);
    const sheet = workbook.worksheets.getItem("Sheet1");
    const states = data[spec.key];
    const rows = data.time.map((time, index) => [
      time,
      states[0][index],
      states[1][index],
      states[2][index],
      states[3][index],
    ]);

    const dataRange = sheet.getRange("A3:E900");
    dataRange.values = rows;
    dataRange.format.numberFormat = "0.000000";
    dataRange.format.horizontalAlignment = "center";
    dataRange.format.verticalAlignment = "center";
    dataRange.format.font = { name: "Times New Roman", size: 11 };
    dataRange.format.borders = { preset: "all", style: "thin", color: "#000000" };

    sheet.getRange("A3:A900").format.numberFormat = "0.0";
    sheet.getRange("A3:E900").format.rowHeight = 14;

    const errors = await workbook.inspect({
      kind: "match",
      searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
      options: { useRegex: true, maxResults: 100 },
      summary: `${spec.key} formula error scan`,
    });
    console.log(`--- ${spec.key} errors ---`);
    console.log(errors.ndjson);

    const check = await workbook.inspect({
      kind: "region",
      sheetId: "Sheet1",
      range: "A1:E12",
      maxChars: 5000,
      tableMaxRows: 12,
      tableMaxCols: 5,
    });
    console.log(`--- ${spec.key} top rows ---`);
    console.log(check.ndjson);

    const tail = await workbook.inspect({
      kind: "region",
      sheetId: "Sheet1",
      range: "A895:E900",
      maxChars: 3000,
      tableMaxRows: 6,
      tableMaxCols: 5,
    });
    console.log(`--- ${spec.key} tail rows ---`);
    console.log(tail.ndjson);

    await renderWorkbook(
      workbook,
      path.join(previewDir, `${spec.key}_filled_top.png`),
      "A1:E16",
    );
    await renderWorkbook(
      workbook,
      path.join(previewDir, `${spec.key}_filled_key.png`),
      "A48:E58",
    );
    const output = await SpreadsheetFile.exportXlsx(workbook);
    await output.save(spec.output);
  }
}


async function verifyWorkbooks() {
  const data = JSON.parse(await fs.readFile(dataPath, "utf8"));
  assertResponseData(data);
  const rowsToCheck = [3, 53, 103, 203, 303, 503, 900];

  for (const spec of workbooks) {
    const workbook = await importWorkbook(spec.output);
    const sheet = workbook.worksheets.getItem("Sheet1");
    for (const excelRow of rowsToCheck) {
      const index = excelRow - 3;
      const expected = [
        data.time[index],
        data[spec.key][0][index],
        data[spec.key][1][index],
        data[spec.key][2][index],
        data[spec.key][3][index],
      ];
      const actual = sheet.getRange(`A${excelRow}:E${excelRow}`).values[0];
      actual.forEach((value, column) => {
        if (Math.abs(Number(value) - expected[column]) > 1e-12) {
          throw new Error(
            `${spec.key} 第 ${excelRow} 行第 ${column + 1} 列与数值结果不一致`,
          );
        }
      });
    }

    const used = await workbook.inspect({
      kind: "region",
      sheetId: "Sheet1",
      range: "A1:E900",
      maxChars: 1200,
      tableMaxRows: 3,
      tableMaxCols: 5,
    });
    const errors = await workbook.inspect({
      kind: "match",
      searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
      options: { useRegex: true, maxResults: 100 },
      summary: `${spec.key} exported formula error scan`,
    });
    console.log(`--- ${spec.key} exported range ---`);
    console.log(used.ndjson);
    console.log(`--- ${spec.key} exported errors ---`);
    console.log(errors.ndjson);

    await renderWorkbook(
      workbook,
      path.join(previewDir, `${spec.key}_exported_top.png`),
      "A1:E16",
    );
    await renderWorkbook(
      workbook,
      path.join(previewDir, `${spec.key}_exported_tail.png`),
      "A895:E900",
    );
  }
}


const mode = process.argv[2] ?? "preview";
if (mode === "preview") {
  await previewTemplates();
} else if (mode === "build") {
  await buildWorkbooks();
} else if (mode === "verify") {
  await verifyWorkbooks();
} else {
  throw new Error(`未知模式: ${mode}`);
}
