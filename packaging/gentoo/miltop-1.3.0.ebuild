EAPI=8

DESCRIPTION="Lightweight tile-based terminal system monitor"
HOMEPAGE="https://github.com/milosz-1710/miltop"
SRC_URI="https://github.com/milosz-1710/miltop/archive/refs/tags/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="GPL-3+"
SLOT="0"
KEYWORDS="~amd64 ~arm64 ~x86"

RDEPEND="dev-lang/python
	dev-python/psutil"
BDEPEND=""

src_install() {
	newbin miltop.py miltop
	dodoc README.md CHANGELOG.md
}
