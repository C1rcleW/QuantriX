/** Simple shared state for cross-component communication.

   Phase 1 solution. Will be replaced by React Context or Zustand later.
*/

import type { VariableDetail } from "../api/client";

let _datasetId: string | null = null;
let _variables: VariableDetail[] = [];
let _datasetName = "";
let _nRows = 0;
let _nCols = 0;

export function setCurrentDataset(
  id: string,
  name: string,
  rows: number,
  cols: number,
  vars: VariableDetail[]
) {
  _datasetId = id;
  _datasetName = name;
  _nRows = rows;
  _nCols = cols;
  _variables = vars;
}

export function getCurrentDatasetId(): string | null {
  return _datasetId;
}

export function getCurrentVariables(): VariableDetail[] {
  return _variables;
}

export function getCurrentDatasetInfo() {
  return {
    datasetId: _datasetId,
    name: _datasetName,
    nRows: _nRows,
    nColumns: _nCols,
    variables: _variables,
  };
}
