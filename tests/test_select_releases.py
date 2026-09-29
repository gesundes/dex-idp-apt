import unittest

from scripts.select_releases import select


def release(tag, *, prerelease=False):
    return {"tag_name": tag, "draft": False, "prerelease": prerelease}


class SelectReleasesTest(unittest.TestCase):
    def test_first_run_builds_latest_stable_release(self):
        self.assertEqual(select([release("v2.45.0"), release("v2.46.0", prerelease=True)], set()), ["v2.45.0"])

    def test_revision_change_rebuilds_latest_and_newer_releases(self):
        releases = [release("v2.46.0"), release("v2.45.1"), release("v2.45.0")]
        self.assertEqual(select(releases, {(2, 45, 1)}, {}), ["v2.45.1", "v2.46.0"])

    def test_complete_architectures_do_not_rebuild(self):
        releases = [release("v2.46.0"), release("v2.45.1")]
        current = {(2, 45, 1): {"amd64", "arm64"}}
        self.assertEqual(select(releases, {(2, 45, 1)}, current), ["v2.46.0"])

    def test_missing_architecture_rebuilds_release(self):
        releases = [release("v2.45.1")]
        current = {(2, 45, 1): {"amd64"}}
        self.assertEqual(select(releases, {(2, 45, 1)}, current), ["v2.45.1"])


if __name__ == "__main__":
    unittest.main()
