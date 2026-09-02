---
status: accepted
---

# 明確固定 Qualification 數值語意

最低數量使用 `>=`，明定為嚴格大於的 return 與 profit factor 維持 `>`；交易或 fills 不足是 `fail`，無法取得或重算 evidence 才是 `indeterminate`。正式比較使用十進位數字與固定 rounding，拒絕 NaN 與一般 infinity；只有正毛利且零毛損的 profit factor 可為正無限，並仍須先通過最低交易數。Fold 比例以有交易 folds 為分母並保存 numerator 與 denominator。
