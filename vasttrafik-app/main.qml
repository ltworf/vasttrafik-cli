/* Copyright (C) 2022 Salvo "LtWorf" Tomaselli
*
* vasttrafik-cli is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
* author Salvo "LtWorf" Tomaselli <tiposchi@tiscali.it>
*/

import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Window {
    width: 640
    height: 480
    visible: true
    title: qsTr("Hello World")

    ColumnLayout {
        anchors.fill: parent

        SwipeView {
            id: topswipe
            orientation: "Horizontal"
            currentIndex: 0
            Layout.fillHeight: true
            Layout.fillWidth: true

            Rectangle {
                color: "red"
            }

            Rectangle {
                color: "yellow"
            }

            Rectangle {
                color: "blue"
            }
        }

        Row {
            Layout.fillWidth: true
            Button {
                text: "Stop"
                onClicked: topswipe.currentIndex = 0
            }
            Button {
                text: "Trip"
                onClicked: topswipe.currentIndex = 1
            }
            Button {
                text: "Settings"
                onClicked: topswipe.currentIndex = 2
            }
        }

    }


}
