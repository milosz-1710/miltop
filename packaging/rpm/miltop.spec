Name:           miltop
Version:        %{miltop_version}
Release:        1
Summary:        Lightweight tile-based terminal system monitor
License:        GPL-3.0-or-later
URL:            https://github.com/milosz-1710/miltop
Source0:        miltop.py
Source1:        LICENSE
Source2:        README.md
Source3:        CHANGELOG.md
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       python3-psutil
Recommends:     inxi

%description
miltop displays CPU, memory, disk, network and process information in a clean,
keyboard- and mouse-friendly terminal dashboard. It supports English and Polish
and can safely request process termination after confirmation.

%prep

%build

%install
install -Dpm0755 %{SOURCE0} %{buildroot}%{_bindir}/miltop
install -Dpm0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
install -Dpm0644 %{SOURCE2} %{buildroot}%{_docdir}/%{name}/README.md
install -Dpm0644 %{SOURCE3} %{buildroot}%{_docdir}/%{name}/CHANGELOG.md

%check
python3 -m py_compile %{SOURCE0}

%files
%{_bindir}/miltop
%license %{_licensedir}/%{name}/LICENSE
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/CHANGELOG.md

%changelog
* Mon Oct 26 2026 Miłosz <79249752+milosz-1710@users.noreply.github.com> - 1.2.0-1
- Add responsive per-core CPU load view

* Mon Oct 26 2026 Miłosz <79249752+milosz-1710@users.noreply.github.com> - 1.1.0-1
- Initial public package
