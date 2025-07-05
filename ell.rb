class Ell < Formula
    include Language::Python::Virtualenv
  
    desc "The ELL Programming Language Interpreter"
    homepage "https://github.com/yourusername/ell"
    url "https://github.com/yourusername/ell/archive/refs/tags/v1.0.0.tar.gz"
    sha256 "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    license "MIT"
  
    depends_on "python@3.12"
  
    def install
      virtualenv_install_with_resources
      bin.install "bin/ell"
    end
  
    test do
      (testpath/"test.ell").write <<~EOS
        console.puttext("Hello ELL!")
      EOS
      output = shell_output("#{bin}/ell test.ell")
      assert_match "Hello ELL!", output
    end
  end
  