from churn_dashboard.model import evaluate, feature_importance, score_customers, train


def test_model_trains_and_beats_baseline(df):
    model, X_test, y_test = train(df)
    report = evaluate(model, X_test, y_test)
    assert report.roc_auc > 0.80
    assert report.pr_auc > y_test.mean() * 2  # well above the no-skill baseline
    probs = score_customers(model, df.head(50))
    assert probs.between(0, 1).all()
    assert len(feature_importance(model, top_n=5)) == 5
