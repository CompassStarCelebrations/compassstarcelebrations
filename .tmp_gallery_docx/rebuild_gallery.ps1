$ErrorActionPreference = 'Stop'

$workspace = 'C:\Rons Documents\Rons Personal Stuff\gitRepos\repo-compassStar\compassstartcelebrations.com\compassstarcelebrations'
$tmp = Join-Path $workspace '.tmp_gallery_docx'
$extract = Join-Path $tmp 'unzipped'
$galleryDir = Join-Path $workspace 'images\gallery'
$galleryHtmlPath = Join-Path $workspace 'gallery.html'

function FixText([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return '' }
    $t = $s.Trim()
    $t = $t -replace 'â€™', '’'
    $t = $t -replace 'Ã©', 'é'
    $t = $t -replace 'MulÃ©', 'Mulé'
    return $t
}

function JsEsc([string]$s) {
    if ($null -eq $s) { return '' }
    return $s.Replace('\\', '\\\\').Replace('"', '\"')
}

[xml]$docXml = Get-Content -Raw (Join-Path $extract 'word\document.xml')
[xml]$relsXml = Get-Content -Raw (Join-Path $extract 'word\_rels\document.xml.rels')

$ns = New-Object System.Xml.XmlNamespaceManager($docXml.NameTable)
$ns.AddNamespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
$ns.AddNamespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')

$relNs = New-Object System.Xml.XmlNamespaceManager($relsXml.NameTable)
$relNs.AddNamespace('rel', 'http://schemas.openxmlformats.org/package/2006/relationships')

$blips = $docXml.SelectNodes('//a:blip[@r:embed]', $ns)
$targets = @()
foreach ($b in $blips) {
    $rid = $b.GetAttribute('embed', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    $rel = $relsXml.SelectSingleNode("//rel:Relationship[@Id='$rid']", $relNs)
    if ($rel) { $targets += $rel.GetAttribute('Target') }
}

$wNs = New-Object System.Xml.XmlNamespaceManager($docXml.NameTable)
$wNs.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
$texts = $docXml.SelectNodes('//w:t', $wNs) | ForEach-Object { $_.InnerText.Trim() } | Where-Object { $_ -ne '' }

$blocks = @()
$i = 0
while ($i -lt $texts.Count) {
    if ($texts[$i] -eq 'Hover -') {
        $title = ''
        $by = ''
        if ($i + 1 -lt $texts.Count) { $title = FixText $texts[$i + 1] }
        if ($i + 2 -lt $texts.Count -and $texts[$i + 2] -ne 'Hover -') { $by = FixText $texts[$i + 2] }

        if ($title -ne 'Renewing Their Vows!') {
            $blocks += [pscustomobject]@{ title = $title; byline = $by }
        }
        $i += 3
    }
    else {
        $i++
    }
}

Get-ChildItem -Path $galleryDir -File -Filter 'gallery-*' -ErrorAction SilentlyContinue | Remove-Item -Force

$items = @()
for ($n = 0; $n -lt $targets.Count; $n++) {
    $target = $targets[$n]
    $src = Join-Path $extract ('word\' + $target.Replace('/', '\'))
    if (-not (Test-Path $src)) { continue }

    $ext = [IO.Path]::GetExtension($src).ToLowerInvariant()
    $name = ('gallery-{0:D2}{1}' -f ($n + 1), $ext)
    Copy-Item $src (Join-Path $galleryDir $name) -Force

    $cap = if ($n -lt $blocks.Count) { $blocks[$n] } else { [pscustomobject]@{ title = ''; byline = '' } }
    $items += [pscustomobject]@{
        src = ('images/gallery/' + $name)
        title = $cap.title
        byline = $cap.byline
    }
}

$gridLines = $items | ForEach-Object { '            <div class="gallery-item"><img src="' + $_.src + '" alt=""></div>' }
$gridMarkup = "<div class=\"gallery-grid\">`r`n" + ($gridLines -join "`r`n") + "`r`n        </div>"

$capLines = $items | ForEach-Object { '                { title: "' + (JsEsc $_.title) + '", byline: "' + (JsEsc $_.byline) + '" }' }
$capArray = "const captions = [`r`n" + ($capLines -join ",`r`n") + "`r`n            ];"

$html = Get-Content -Raw $galleryHtmlPath

$gridStart = $html.IndexOf('<div class="gallery-grid">')
$gridEndToken = "`r`n        </div>"
$gridEnd = $html.IndexOf($gridEndToken, $gridStart)
if ($gridStart -ge 0 -and $gridEnd -ge 0) {
    $before = $html.Substring(0, $gridStart)
    $after = $html.Substring($gridEnd + $gridEndToken.Length)
    $html = $before + $gridMarkup + $after
}

$capStart = $html.IndexOf('const captions = [')
$capEndToken = "`r`n            ];"
$capEnd = $html.IndexOf($capEndToken, $capStart)
if ($capStart -ge 0 -and $capEnd -ge 0) {
    $beforeCap = $html.Substring(0, $capStart)
    $afterCap = $html.Substring($capEnd + $capEndToken.Length)
    $html = $beforeCap + $capArray + $afterCap
}

Set-Content -Path $galleryHtmlPath -Value $html -Encoding UTF8

$items | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $tmp 'gallery_data.json') -Encoding UTF8

Write-Output ("images={0} captions={1}" -f $items.Count, $blocks.Count)
