import io
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

def draw_chart(symbol, df):
    # Remove timezone info from datetime index to avoid offset issues
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    buf = io.BytesIO()

    mc = mpf.make_marketcolors(
        up='#00ff99',
        down='#ff4d4d',
        edge='inherit',
        wick={'up': '#00ff99', 'down': '#ff4d4d'},
        volume={'up': '#00ff99', 'down': '#ff4d4d'},
        ohlc='inherit'
    )

    style = mpf.make_mpf_style(
        base_mpf_style='binance',
        marketcolors=mc,
        facecolor='#000000',
        edgecolor='#000000',
        figcolor='#000000',
        gridcolor='#222222',
        rc={
            'axes.labelcolor': '#CCCCCC',
            'xtick.color': '#AAAAAA',
            'ytick.color': '#AAAAAA',
            'axes.edgecolor': '#333333',
            'savefig.facecolor': '#000000',
            'savefig.edgecolor': '#000000',
        }
    )

    # Custom legend labels for the moving averages and volume
    mav_labels = ['SMA 50', 'SMA 200']
    volume_label = 'Объём'  # Volume label in Russian or change to English if preferred

    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=(50, 200),
        volume=True,
        title=f"{symbol} Price (USDT)",
        style=style,
        returnfig=True,
        figsize=(10, 6),
        tight_layout=True,
    )

    # axlist contains: [price_ax, volume_ax]
    price_ax = axlist[0]
    volume_ax = axlist[2] if len(axlist) > 2 else None

    # Set black backgrounds explicitly (in case)
    for ax in axlist:
        ax.set_facecolor('#000000')
    fig.patch.set_facecolor('#000000')

    # Add legend for price plot (candles + SMA lines)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    candle_patch = Patch(facecolor='#00ff99', edgecolor='#00ff99', label='Рост цены (Candle Up)')
    candle_down_patch = Patch(facecolor='#ff4d4d', edgecolor='#ff4d4d', label='Падение цены (Candle Down)')
    sma50_line = Line2D([0], [0], color='orange', label=mav_labels[0])
    sma200_line = Line2D([0], [0], color='cyan', label=mav_labels[1])

    legend_handles = [candle_patch, candle_down_patch, sma50_line, sma200_line]
    legend = price_ax.legend(
        handles=legend_handles,
        loc='upper left',
        fontsize=9,
        facecolor='#111111',
        edgecolor='#444444'
    )

    # Set legend text color to white
    for text in legend.get_texts():
        text.set_color('white')

    # Add legend to volume axis if exists
    if volume_ax is not None:
        vol_patch_up = Patch(color='#00ff99', label=volume_label + ' (Рост)')
        vol_patch_down = Patch(color='#ff4d4d', label=volume_label + ' (Падение)')
        vol_legend = volume_ax.legend(
            handles=[vol_patch_up, vol_patch_down],
            loc='upper right',
            fontsize=9,
            facecolor='#111111',
            edgecolor='#444444'
        )

        for text in vol_legend.get_texts():
            text.set_color('white')

    fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#000000')
    plt.close(fig)
    buf.seek(0)
    return buf
