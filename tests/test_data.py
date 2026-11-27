import numpy as np
import pandas as pd
import pytest

from modules import data as D


def _fake_df(n_artists=30, per=100):
    rows = [
        {"artist": f"A{i:02d}", "style": "s", "genre": "g"}
        for i in range(n_artists)
        for _ in range(per)
    ]
    return pd.DataFrame(rows)


# ── #3: 화가 선별·분할 (모델 없이 실행) ──
def test_select_artists_count_and_deterministic():
    df = _fake_df()
    a = D.select_artists(df, n=24)
    assert len(a) == 24 and a == D.select_artists(df, n=24)


def test_select_artists_too_few_raises():
    with pytest.raises(ValueError):
        D.select_artists(_fake_df(n_artists=5), n=24)


def test_select_artists_excludes_unknown():
    df = pd.concat(
        [_fake_df(3), pd.DataFrame({"artist": ["Unknown Artist"] * 500})], ignore_index=True
    )
    assert "Unknown Artist" not in D.select_artists(df, n=3)


def test_display_name_and_idempotent():
    cases = {
        "vincent-van-gogh": "Vincent van Gogh",
        "pierre-auguste-renoir": "Pierre-Auguste Renoir",
        "claude-monet": "Claude Monet",
        "rembrandt": "Rembrandt",
        "john-singer-sargent": "John Singer Sargent",
    }
    for slug, shown in cases.items():
        assert D.display_name(slug) == shown
        assert D.display_name(shown) == shown  # 이미 표시용이면 그대로


def test_load_index_uses_display_names(tmp_path):
    np.save(tmp_path / "embeddings.npy", np.zeros((2, 512), np.float32))
    pd.DataFrame(
        {
            "id": ["000001", "000002"],
            "artist": ["vincent-van-gogh", "rembrandt"],
            "style": "s",
            "genre": "g",
            "path": "p",
            "split": "train",
        }
    ).to_csv(tmp_path / "meta.csv", index=False)
    idx = D.load_index(tmp_path)
    assert list(idx["meta"]["artist"]) == ["Vincent van Gogh", "Rembrandt"]
    assert list(idx["meta"].columns) == ["id", "artist", "style", "genre", "path", "split"]


def test_team_constants_and_fake_fallback(tmp_path):
    assert len(D.ARTISTS) == 23 and len(set(D.ARTISTS)) == 23
    idx = D.load_index(tmp_path)  # 빈 폴더 -> 가짜 인덱스
    assert idx["meta"].attrs["fake"] is True
    assert idx["emb"].shape == (23 * D.WORKS_PER_ARTIST, 512)
    assert list(idx["meta"].columns) == ["id", "artist", "style", "genre", "path", "split"]
    assert set(idx["meta"]["artist"]) == set(D.ARTISTS)


def test_clip_keywords_stub_shape():
    out = D.clip_keywords(np.ones(512, np.float32), k=3)
    assert len(out) == 3 and out == sorted(out, key=lambda t: -t[1])


def test_cap_per_artist_keeps_columns_and_caps():
    df = pd.DataFrame({"artist": ["a"] * 10 + ["b"] * 3, "style": "s", "genre": "g"})
    r = D.cap_per_artist(df, 5)
    assert list(r.columns) == ["artist", "style", "genre"]
    assert r["artist"].value_counts().to_dict() == {"a": 5, "b": 3}
    assert r.equals(D.cap_per_artist(df, 5))  # 재현 가능
    assert D.cap_per_artist(df, None).equals(df)


def test_split_ratio_and_stratified():
    df = D.split_dataframe(_fake_df(24, 100))
    assert set(df["split"]) == set(D.SPLIT_NAMES)
    frac = df["split"].value_counts(normalize=True)
    assert (
        abs(frac["train"] - 0.70) < 0.02
        and abs(frac["val"] - 0.15) < 0.02
        and abs(frac["test"] - 0.15) < 0.02
    )
    # 모든 화가가 세 split에 모두 존재
    assert (df.groupby("artist")["split"].nunique() == 3).all()


def test_split_reproducible_and_no_overlap():
    base = _fake_df(24, 100)
    s1, s2 = D.split_dataframe(base), D.split_dataframe(base)
    assert s1["split"].equals(s2["split"])
    assert s1["split"].notna().all()  # 한 행은 정확히 하나의 split


# ── #5: 임베딩 (CLIP 모델이 받아지는 환경에서만 실행) ──
@pytest.fixture(scope="module")
def clip_ready():
    try:
        D._get_clip()
    except Exception as e:  # noqa: BLE001 - 모델 다운로드 불가 등 원인이 다양해 모두 건너뜀 처리
        pytest.skip(f"CLIP 로드 불가: {e}")


@pytest.mark.model
def test_embed_image_shape_norm_and_same_image(clip_ready):
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (300, 400, 3), dtype=np.uint8)
    a, b = D.embed_image(img), D.embed_image(img)
    assert a.shape == (512,)
    assert abs(np.linalg.norm(a) - 1) < 1e-4
    assert float(a @ b) >= 0.99  # 이슈 #5 완료 기준


@pytest.mark.model
def test_embed_text_shape_norm(clip_ready):
    t = D.embed_text(["vivid colors", "muted colors"])
    assert t.shape == (2, 512)
    assert np.allclose(np.linalg.norm(t, axis=1), 1, atol=1e-4)


@pytest.mark.model
def test_embed_image_rejects_bad_input(clip_ready):
    with pytest.raises(ValueError):
        D.embed_image(np.zeros((10, 10), dtype=np.uint8))


def test_load_index_cache(tmp_path):
    """같은 파일은 캐시에서 읽고, meta는 복사본이며, 파일이 바뀌면 다시 읽는다."""
    import numpy as np
    import pandas as pd

    def write(n):
        pd.DataFrame(
            {
                "id": [f"{i:06d}" for i in range(n)],
                "artist": ["vincent-van-gogh"] * n,
                "style": ["Post_Impressionism"] * n,
                "genre": ["landscape"] * n,
                "path": ["x.jpg"] * n,
                "split": ["train"] * n,
            }
        ).to_csv(tmp_path / "meta.csv", index=False)
        np.save(tmp_path / "embeddings.npy", np.ones((n, 512), dtype=np.float32))

    write(3)
    a = D.load_index(tmp_path)
    b = D.load_index(tmp_path)
    assert a["emb"] is b["emb"]  # 한 번만 읽음
    assert a["meta"] is not b["meta"]  # meta는 호출마다 복사본
    assert a["meta"].attrs["fake"] is False  # copy 후에도 fake 표시 유지
    a["meta"].loc[0, "artist"] = "changed"
    assert D.load_index(tmp_path)["meta"].loc[0, "artist"] == "Vincent van Gogh"
    write(5)  # 파일이 바뀌면 다시 읽는다
    assert len(D.load_index(tmp_path)["emb"]) == 5


def test_artist_info_covers_index():
    """실제 인덱스의 모든 화가에게 소개가 있고, 빈 칸이 없다."""
    idx = D.load_index()
    if idx["meta"].attrs["fake"]:
        pytest.skip("실제 인덱스가 없는 환경")
    info = D.load_artist_info()
    assert set(idx["meta"]["artist"]) <= set(info)
    for name, row in info.items():
        assert all(row[k].strip() for k in ("years", "nationality", "intro")), name
        assert len(row["intro"]) <= 120, name  # 화면에 한두 줄로 보이는 길이


def test_artist_info_missing_file(tmp_path):
    assert D.load_artist_info(tmp_path / "none.csv") == {}
