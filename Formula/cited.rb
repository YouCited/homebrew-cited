class Cited < Formula
  include Language::Python::Virtualenv

  desc "CLI for the Cited GEO platform"
  homepage "https://youcited.com"
  # url "https://github.com/YouCited/cited-cli/releases/download/v0.1.0/cited_cli-0.1.0.tar.gz"
  # sha256 "PLACEHOLDER"
  license "Proprietary"

  depends_on "python@3.12"

  # Generate dependency resources with:
  #   pip install homebrew-pypi-poet
  #   poet cited-cli

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "cited-cli", shell_output("#{bin}/cited version")
  end
end
