# analyze_my_winrate.py
import os
import argparse
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn import model_selection, metrics

CSV_PATH = "data/my_matches_ml.csv"
MODEL_PATH = "data/my_win_model.joblib"

# ---- utility ----
def normalize_role(s: str) -> str:
    s = (s or "").upper()
    if s in ("BOTTOM", "BOT"):
        return "ADC"
    if s in ("UTILITY",):
        return "SUPPORT"
    if s == "MIDDLE":
        return "MID"
    return s or "UNKNOWN"

def to_patch(ver: str) -> str:
    # "14.20.123" -> "14.20"
    if not isinstance(ver, str) or "." not in ver:
        return ""
    p = ver.split(".")
    return f"{p[0]}.{p[1]}" if len(p) >= 2 else ver

def load_df(path=CSV_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} 가 없습니다. 먼저 CSV 생성 스크립트를 실행하세요.")
    df = pd.read_csv(path, encoding="utf-8-sig").copy()

    for c in ["champion", "role", "runePrimary", "runeSub", "win"]:
        if c not in df.columns:
            raise ValueError(f"CSV에 '{c}' 컬럼이 없습니다.")

    df["role"] = df["role"].astype(str).map(normalize_role)
    df["patch"] = df.get("gameVersion", "").astype(str).map(to_patch)

    # fill empty
    df = df.fillna(0)
    return df

def build_pipeline(cat_cols, num_cols):
    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )
    model = Pipeline(steps=[
        ("prep", preprocess),
        ("clf", RandomForestClassifier(
            n_estimators=300, max_depth=12, random_state=42, n_jobs=-1
        ))
    ])
    return model

# ---- Defaults & Averages ----
NUM_COLS_ALL = [
    "kills","deaths","assists",
    "goldPerMin","csPerMin","dmgPerMin","visionScore","xpPerMin"
]
CAT_COLS_ALL = ["champion", "role", "runePrimary", "runeSub", "queueId", "patch"]

def _safe_mode(series, default=None):
    if len(series) == 0:
        return default
    s = series.dropna()
    if s.empty:
        return default
    return s.mode().iloc[0]

def get_feature_defaults(df: pd.DataFrame) -> dict:
    """전체 데이터의 평균/최빈값으로 기본 피처 생성"""
    defaults = {}
    for c in NUM_COLS_ALL:
        if c in df.columns:
            defaults[c] = float(df[c].mean())
        else:
            defaults[c] = 0.0

    defaults["runePrimary"] = int(_safe_mode(df["runePrimary"], 8000))
    defaults["runeSub"]     = int(_safe_mode(df["runeSub"], 8300))
    defaults["role"]        = normalize_role(str(_safe_mode(df["role"], "ADC")))
    defaults["queueId"]     = int(_safe_mode(df["queueId"], 420))
    defaults["patch"]       = str(_safe_mode(df["patch"], ""))

    return defaults

def get_champion_avg(df: pd.DataFrame, champion: str) -> dict | None:
    """해당 챔피언으로 플레이한 평균/최빈값으로 피처 구성. 없으면 None."""
    sub = df[df["champion"] == champion]
    if sub.empty:
        return None

    defaults = {}
    for c in NUM_COLS_ALL:
        if c in sub.columns:
            defaults[c] = float(sub[c].mean())
        else:
            defaults[c] = 0.0

    defaults["runePrimary"] = int(_safe_mode(sub["runePrimary"], _safe_mode(df["runePrimary"], 8000)))
    defaults["runeSub"]     = int(_safe_mode(sub["runeSub"], _safe_mode(df["runeSub"], 8300)))
    defaults["role"]        = normalize_role(str(_safe_mode(sub["role"], _safe_mode(df["role"], "ADC"))))
    defaults["queueId"]     = int(_safe_mode(sub["queueId"], _safe_mode(df["queueId"], 420)))
    defaults["patch"]       = str(_safe_mode(sub["patch"], _safe_mode(df["patch"], "")))

    return defaults

# ---- Train / Evaluate / Predict ----
def train_and_eval(df, save_model=True, model_path=MODEL_PATH, test_size=0.2, random_state=42):
    cat_cols = CAT_COLS_ALL.copy()
    num_cols = [c for c in NUM_COLS_ALL if c in df.columns]

    X = df[cat_cols + num_cols].copy()
    y = df["win"].astype(int)

    X_tr, X_te, y_tr, y_te = model_selection.train_test_split(
        X, y, test_size=test_size, random_state=random_state,
        stratify=y if y.nunique() == 2 else None
    )

    pipe = build_pipeline(cat_cols, num_cols)
    pipe.fit(X_tr, y_tr)

    pred = pipe.predict(X_te)
    proba = pipe.predict_proba(X_te)[:, 1] if hasattr(pipe.named_steps["clf"], "predict_proba") else None

    acc = metrics.accuracy_score(y_te, pred)
    roc = metrics.roc_auc_score(y_te, proba) if proba is not None else None
    f1  = metrics.f1_score(y_te, pred)

    if save_model:
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(pipe, model_path)

    return {"acc": acc, "roc_auc": roc, "f1": f1, "n_train": len(X_tr), "n_test": len(X_te)}

def predict_sample(model_path, champion, role, rune_primary, rune_sub,
                   kills, deaths, assists, gold_per_min, cs_per_min,
                   dmg_per_min, vision_score, xp_per_min,
                   queue_id=None, patch=None):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"모델이 없습니다: {model_path} (먼저 --train 실행)")
    pipe = joblib.load(model_path)

    role = normalize_role(role)

    row = {
        "champion": str(champion),
        "role": role,
        "runePrimary": int(rune_primary),
        "runeSub": int(rune_sub),
        "kills": float(kills),
        "deaths": float(deaths),
        "assists": float(assists),
        "goldPerMin": float(gold_per_min),
        "csPerMin": float(cs_per_min),
        "dmgPerMin": float(dmg_per_min),
        "visionScore": float(vision_score),
        "xpPerMin": float(xp_per_min),
        "queueId": int(queue_id) if queue_id is not None else 0,
        "patch": str(patch) if patch is not None else "",
    }

    X = pd.DataFrame([row])
    proba = pipe.predict_proba(X)[:, 1][0]
    pred  = int(proba >= 0.5)
    return {"prob_win": proba, "pred_win": pred}

# ---- CLI ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true", help="모델 학습/평가 후 저장")
    ap.add_argument("--csv", default=CSV_PATH, help="CSV 경로")
    ap.add_argument("--model", default=MODEL_PATH, help="모델 저장/로드 경로")

    ap.add_argument("--champion")
    ap.add_argument("--role")
    ap.add_argument("--runePrimary", type=int)
    ap.add_argument("--runeSub", type=int)
    ap.add_argument("--kills", type=float)
    ap.add_argument("--deaths", type=float)
    ap.add_argument("--assists", type=float)
    ap.add_argument("--goldPerMin", type=float)
    ap.add_argument("--csPerMin", type=float)
    ap.add_argument("--dmgPerMin", type=float)
    ap.add_argument("--visionScore", type=float)
    ap.add_argument("--xpPerMin", type=float)
    ap.add_argument("--queueId", type=int)
    ap.add_argument("--patch")

    args = ap.parse_args()

    # traing
    if args.train:
        df = load_df(args.csv)
        report = train_and_eval(df, save_model=True, model_path=args.model)
        print(f"[TRAIN] n_train={report['n_train']}  n_test={report['n_test']}")
        print(f"  - acc: {report['acc']:.3f}")
        if report["roc_auc"] is not None:
            print(f"  - roc_auc: {report['roc_auc']:.3f}")
        print(f"  - f1: {report['f1']:.3f}")

    # predict
    provided = [
        args.champion, args.role, args.runePrimary, args.runeSub,
        args.kills, args.deaths, args.assists, args.goldPerMin,
        args.csPerMin, args.dmgPerMin, args.visionScore, args.xpPerMin
    ]

    if args.champion is not None:
        if all(v is not None for v in provided):
            # all input
            out = predict_sample(
                args.model, args.champion, args.role, args.runePrimary, args.runeSub,
                args.kills, args.deaths, args.assists, args.goldPerMin, args.csPerMin,
                args.dmgPerMin, args.visionScore, args.xpPerMin,
                queue_id=args.queueId, patch=args.patch
            )
            print(f"[PREDICT] prob_win={out['prob_win']*100:.1f}%  pred_win={out['pred_win']}")
        else:
            # some input
            df = load_df(args.csv)
            # role normalize
            role_in = normalize_role(args.role) if args.role else None

            # champion mean
            defaults = get_champion_avg(df, args.champion)
            used = "champion_avg"
            if defaults is None:
                defaults = get_feature_defaults(df)
                used = "global_defaults"

            # input data and defaults
            role_final        = role_in or defaults["role"]
            rune_primary_final= args.runePrimary if args.runePrimary is not None else defaults["runePrimary"]
            rune_sub_final    = args.runeSub     if args.runeSub     is not None else defaults["runeSub"]
            kills_final       = args.kills       if args.kills       is not None else defaults["kills"]
            deaths_final      = args.deaths      if args.deaths      is not None else defaults["deaths"]
            assists_final     = args.assists     if args.assists     is not None else defaults["assists"]
            gpm_final         = args.goldPerMin  if args.goldPerMin  is not None else defaults["goldPerMin"]
            cspm_final        = args.csPerMin    if args.csPerMin    is not None else defaults["csPerMin"]
            dpm_final         = args.dmgPerMin   if args.dmgPerMin   is not None else defaults["dmgPerMin"]
            vs_final          = args.visionScore if args.visionScore is not None else defaults["visionScore"]
            xp_final          = args.xpPerMin    if args.xpPerMin    is not None else defaults["xpPerMin"]
            queue_final       = args.queueId     if args.queueId     is not None else defaults["queueId"]
            patch_final       = args.patch       if args.patch       is not None else defaults["patch"]

            out = predict_sample(
                args.model, args.champion, role_final, rune_primary_final, rune_sub_final,
                kills_final, deaths_final, assists_final, gpm_final, cspm_final,
                dpm_final, vs_final, xp_final,
                queue_id=queue_final, patch=patch_final
            )
            print(f"[PREDICT*] prob_win={out['prob_win']*100:.1f}%  pred_win={out['pred_win']}  (fill={used})")

if __name__ == "__main__":
    main()
